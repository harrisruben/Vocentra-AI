import asyncio
import datetime
import time
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.models import Campaign, CampaignLead, Organization
from app.services import get_voice_provider
from app.core.logger import logger
from app.voice.websocket.websocket import manager as ws_manager
from app.voice.session_manager import SessionManager
from app.voice.transcripts.transcripts import broadcast_active_calls

async def broadcast_campaign_progress(campaign_id: int, db: AsyncSession):
    """Compile and broadcast campaign progress stats via WebSockets."""
    try:
        campaign = await db.get(Campaign, campaign_id)
        if not campaign:
            return
            
        status_query = select(CampaignLead.status, func.count(CampaignLead.id)).filter(CampaignLead.campaign_id == campaign_id).group_by(CampaignLead.status)
        status_res = await db.execute(status_query)
        status_counts = dict(status_res.all())
        
        # Calculate success rate & details
        total_leads = campaign.lead_count
        completed = campaign.completed_count
        failed = campaign.failed_count
        running = status_counts.get("calling", 0) + status_counts.get("in_progress", 0)
        queued = status_counts.get("queued", 0)
        
        # Average duration & costs from completed leads
        stats_query = select(
            func.avg(CampaignLead.duration),
            func.avg(CampaignLead.cost),
            func.sum(CampaignLead.cost)
        ).filter(CampaignLead.campaign_id == campaign_id, CampaignLead.status == "completed")
        stats_res = await db.execute(stats_query)
        avg_dur, avg_cost, total_cost = stats_res.first()
        
        # Success rate is completed leads divided by completed + failed
        total_finished = completed + failed
        success_rate = (completed / total_finished * 100) if total_finished > 0 else 0
        completion_pct = (total_finished / total_leads * 100) if total_leads > 0 else 0

        # Load settings to get call delay for ETA
        org_res = await db.execute(select(Organization).filter(Organization.id == campaign.organization_id))
        org = org_res.scalar()
        call_delay = org.call_delay if org and org.call_delay is not None else 30
        eta_seconds = (queued * (avg_dur or 45 + call_delay)) if queued > 0 else 0

        message = {
            "type": "campaign_progress",
            "data": {
                "campaign_id": campaign.id,
                "status": campaign.status,
                "lead_count": total_leads,
                "completed_count": completed,
                "failed_count": failed,
                "running_count": running,
                "queued_count": queued,
                "success_rate": round(success_rate, 1),
                "completion_pct": round(completion_pct, 1),
                "avg_duration": round(avg_dur or 0, 1),
                "avg_cost": round(avg_cost or 0, 3),
                "total_cost": round(total_cost or 0, 3),
                "eta_seconds": int(eta_seconds)
            }
        }
        await ws_manager.broadcast_dashboard(campaign.organization_id, message)
        logger.info(f"Campaign Worker: Broadcasted campaign {campaign_id} progress to org {campaign.organization_id}")
    except Exception as e:
        logger.error(f"Campaign Worker: Failed to broadcast progress for campaign {campaign_id}: {str(e)}", exc_info=True)

async def process_campaign(campaign_id: int):
    """Processes campaign leads sequentially in the background."""
    logger.info(f"Campaign Worker: Sequential processing loop started for campaign_id={campaign_id}")
    
    while True:
        async with AsyncSessionLocal() as db:
            # 1. Fetch Campaign and verify status
            campaign_res = await db.execute(select(Campaign).filter(Campaign.id == campaign_id))
            campaign = campaign_res.scalar()
            if not campaign:
                logger.error(f"Campaign Worker: Campaign {campaign_id} not found. Terminating execution.")
                break
                
            if campaign.status != "running":
                logger.info(f"Campaign Worker: Campaign {campaign_id} status is '{campaign.status}'. Stopping sequential processor.")
                break
                
            # 2. Fetch Organization credentials & settings
            org_res = await db.execute(select(Organization).filter(Organization.id == campaign.organization_id))
            org = org_res.scalar()
            if not org:
                logger.error(f"Campaign Worker: Organization {campaign.organization_id} not found. Terminating.")
                break
                
            assistant_id = org.vapi_assistant_id or "vapi_assistant_mock_id"
            call_delay = org.call_delay if org.call_delay is not None else 30
            
            # 3. Find the next pending lead
            lead_res = await db.execute(
                select(CampaignLead)
                .filter(CampaignLead.campaign_id == campaign_id, CampaignLead.status == "queued")
                .order_by(CampaignLead.id.asc())
                .limit(1)
            )
            lead = lead_res.scalar()
            
            if not lead:
                # No more queued leads. Check if there are active calls
                active_res = await db.execute(
                    select(CampaignLead).filter(CampaignLead.campaign_id == campaign_id, CampaignLead.status == "calling")
                )
                active_leads = active_res.scalars().all()
                if not active_leads:
                    campaign.status = "completed"
                    campaign.completed_at = datetime.datetime.utcnow()
                    await db.commit()
                    logger.info(f"Campaign Worker: Campaign {campaign_id} has no more leads. Marked as completed.")
                    await broadcast_campaign_progress(campaign_id, db)
                else:
                    logger.info(f"Campaign Worker: Campaign {campaign_id} waiting for {len(active_leads)} active calls to finish.")
                break
                
            # 4. Set lead status to Calling and update attempts
            lead.status = "calling"
            lead.attempts += 1
            await db.commit()
            await db.refresh(lead)
            
            await broadcast_campaign_progress(campaign_id, db)
            
            # Resolve outbound phone number
            voice_provider = get_voice_provider()
            phone_number_id = None
            try:
                phones = await voice_provider.get_phone_numbers()
                for p in phones:
                    p_num = p.get("number", "")
                    clean_p = "".join(c for c in p_num if c.isdigit() or c == "+")
                    clean_target = "".join(c for c in "+19843712375" if c.isdigit() or c == "+")
                    if clean_p == clean_target:
                        phone_number_id = p.get("id")
                        break
                if not phone_number_id and phones:
                    phone_number_id = phones[0].get("id")
            except Exception as e:
                logger.error(f"Campaign Worker: Error checking phone number IDs: {str(e)}")
                
            # 5. Start call via provider with retry threshold
            metadata = {
                "campaign_id": campaign.id,
                "lead_id": lead.id,
                "org_id": campaign.organization_id
            }
            
            max_retries = 3
            vapi_call_id = None
            call_res = None
            last_err = None
            
            for attempt in range(max_retries):
                try:
                    call_res = await voice_provider.start_call(
                        assistant_id=assistant_id,
                        phone_number_id=phone_number_id,
                        customer_number=lead.phone,
                        metadata=metadata
                    )
                    vapi_call_id = call_res.get("id")
                    if vapi_call_id:
                        break
                except Exception as ex:
                    last_err = str(ex)
                    logger.warn(f"Campaign Worker: start_call attempt {attempt + 1} failed: {last_err}")
                    await asyncio.sleep(2)
                    
            if not vapi_call_id:
                # If outbound trigger failed completely, mark lead failed and continue
                lead.status = "failed"
                lead.last_error = f"Start call failed: {last_err}"
                campaign.failed_count += 1
                await db.commit()
                await broadcast_campaign_progress(campaign_id, db)
                logger.error(f"Campaign Worker: Failed to start call for lead {lead.id}. Continuing sequentially.")
                await asyncio.sleep(call_delay)
                continue
                
            # Pre-populate lead execution metrics
            lead.vapi_call_id = vapi_call_id
            lead.assistant_id = assistant_id
            lead.phone_number_id = phone_number_id
            lead.started_at = datetime.datetime.utcnow()
            await db.commit()
            
            # Setup active call dashboard telemetry
            state = SessionManager.get_session(vapi_call_id)
            state["last_utterance"] = "Outbound campaign call connected. Ready."
            state["customer_name"] = lead.name or "Lead"
            state["customer_phone"] = lead.phone
            state["active_intent"] = f"Campaign Outbound"
            
            await broadcast_active_calls(campaign.organization_id, db)
            await broadcast_campaign_progress(campaign_id, db)
            
            # 6. Poll for call execution completion
            logger.info(f"Campaign Worker: Outbound call triggered (id={vapi_call_id}). Polling state...")
            is_mock = vapi_call_id.startswith(("vapi_outbound_", "mock_"))
            
            call_finished = False
            start_poll = time.time()
            poll_timeout = 900 # 15 minutes max duration
            
            import sys
            is_testing = "pytest" in sys.modules
            if is_mock:
                # Simulated call in offline/dev environments
                if not is_testing:
                    await asyncio.sleep(4)
                call_finished = True
                async with AsyncSessionLocal() as fin_db:
                    lead_fin = await fin_db.get(CampaignLead, lead.id)
                    if lead_fin:
                        lead_fin.status = "completed"
                        lead_fin.ended_at = datetime.datetime.utcnow()
                        lead_fin.duration = 15
                        lead_fin.cost = 0.05
                        lead_fin.recording_url = "https://api.vapi.ai/mock-recording.mp3"
                        lead_fin.summary = "Outbound mock campaign call finalized successfully."
                        lead_fin.transcript = "Assistant: Hello, this is Vocentra AI outbound campaign call. How can I help?\nCustomer: All good, thanks!"
                        lead_fin.ended_reason = "customer-ended-call"
                        
                        camp_fin = await fin_db.get(Campaign, campaign_id)
                        if camp_fin:
                            camp_fin.completed_count += 1
                        await fin_db.commit()
            else:
                # Real call: wait for webhook EndOfCallReport or poll Vapi API directly
                while (time.time() - start_poll) < poll_timeout:
                    # Check database (webhook might have already processed call and marked lead)
                    async with AsyncSessionLocal() as check_db:
                        lead_check = await check_db.get(CampaignLead, lead.id)
                        if lead_check and lead_check.status in ["completed", "failed"]:
                            call_finished = True
                            break
                            
                    # Poll Vapi directly
                    try:
                        vapi_detail = await voice_provider.get_call(vapi_call_id)
                        v_status = (vapi_detail.get("status") or "").lower()
                        if v_status in ["ended", "failed", "completed"]:
                            async with AsyncSessionLocal() as fin_db:
                                lead_fin = await fin_db.get(CampaignLead, lead.id)
                                if lead_fin:
                                    lead_fin.status = "completed" if v_status in ["ended", "completed"] else "failed"
                                    lead_fin.ended_at = datetime.datetime.utcnow()
                                    lead_fin.duration = vapi_detail.get("duration", 0)
                                    lead_fin.cost = vapi_detail.get("cost", 0.0)
                                    lead_fin.recording_url = vapi_detail.get("recordingUrl")
                                    lead_fin.summary = vapi_detail.get("summary")
                                    lead_fin.transcript = vapi_detail.get("transcript")
                                    lead_fin.ended_reason = vapi_detail.get("endedReason", "customer-ended-call")
                                    
                                    camp_fin = await fin_db.get(Campaign, campaign_id)
                                    if camp_fin:
                                        if lead_fin.status == "completed":
                                            camp_fin.completed_count += 1
                                        else:
                                            camp_fin.failed_count += 1
                                    await fin_db.commit()
                            call_finished = True
                            break
                    except Exception as poll_ex:
                        logger.error(f"Campaign Worker: Poller error: {str(poll_ex)}")
                        
                    await asyncio.sleep(4)
                    
                if not call_finished:
                    # Timeout fallback
                    async with AsyncSessionLocal() as fin_db:
                        lead_fin = await fin_db.get(CampaignLead, lead.id)
                        if lead_fin:
                            lead_fin.status = "failed"
                            lead_fin.last_error = "Call timed out."
                            camp_fin = await fin_db.get(Campaign, campaign_id)
                            if camp_fin:
                                camp_fin.failed_count += 1
                            await fin_db.commit()
                            
            SessionManager.clear_session(vapi_call_id)
            async with AsyncSessionLocal() as broadcast_db:
                await broadcast_active_calls(campaign.organization_id, broadcast_db)
                await broadcast_campaign_progress(campaign_id, broadcast_db)
                
            # 7. Apply call delay
            import sys
            if "pytest" not in sys.modules:
                logger.info(f"Campaign Worker: Sequential call finished. Sleeping for delay={call_delay} seconds...")
                await asyncio.sleep(call_delay)


async def enqueue_campaign_job(campaign_id: int):
    """Enqueues campaign sequentially via ARQ worker or asyncio.create_task fallback."""
    from arq import create_pool
    from arq.connections import RedisSettings
    from app.core.config import settings
    
    import sys
    # In testing environment, run synchronously for fast and predictable test assertions
    if "pytest" in sys.modules:
        logger.info(f"Campaign Worker: Testing mode. Processing campaign {campaign_id} synchronously.")
        await process_campaign(campaign_id)
        return True

    # Try enqueuing to Redis/ARQ
    try:
        redis_url = settings.REDIS_URL or "redis://localhost:6379/0"
        import urllib.parse
        parsed = urllib.parse.urlparse(redis_url)
        redis_host = parsed.hostname or "localhost"
        redis_port = parsed.port or 6379
        
        redis_settings = RedisSettings(host=redis_host, port=redis_port)
        pool = await create_pool(redis_settings)
        await pool.enqueue_job('execute_background_job', 'process_campaign', {'campaign_id': campaign_id})
        await pool.close()
        logger.info(f"Campaign Worker: Enqueued campaign {campaign_id} to ARQ worker.")
        return True
    except Exception as e:
        logger.warning(f"Campaign Worker: Failed to queue campaign via Redis/ARQ ({str(e)}). Falling back to in-process background task.")
        # Fallback: Run in-process using asyncio.create_task
        asyncio.create_task(process_campaign(campaign_id))
        return False
