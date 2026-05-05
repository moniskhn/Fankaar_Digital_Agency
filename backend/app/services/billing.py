"""
Claude Mythos — Stripe Billing Integration
Complete subscription billing: checkout sessions, webhooks, invoices,
billing portal, usage tracking, and revenue metrics.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.config import settings
from app.core.database import SessionLocal, generate_uuid
from app.services.service_catalog import PACKAGES, service_catalog, ServiceCatalog

logger = logging.getLogger(__name__)

# ── Stripe client (lazy import for graceful degradation) ──
_stripe = None


def _get_stripe():
    """Lazy-load Stripe client."""
    global _stripe
    if _stripe is None:
        try:
            import stripe as stripe_lib
            if settings.stripe_secret_key:
                stripe_lib.api_key = settings.stripe_secret_key
                stripe_lib.api_version = "2024-06-20"
                _stripe = stripe_lib
                logger.info("Stripe client initialized")
            else:
                logger.warning("Stripe secret key not configured")
        except ImportError:
            logger.warning("stripe package not installed — billing features disabled")
        except Exception as e:
            logger.error(f"Stripe initialization error: {e}")
    return _stripe


# ═══════════════════════════════════════════════════════════════════
# IN-MEMORY SUBSCRIPTION STORE (with DB persistence)
# ═══════════════════════════════════════════════════════════════════

class SubscriptionStore:
    """Thread-safe subscription storage with DB backing."""

    _subscriptions: Dict[str, Dict[str, Any]] = {}
    _usage: Dict[str, List[Dict[str, Any]]] = {}
    _invoices: Dict[str, List[Dict[str, Any]]] = {}
    _initialized = False

    @classmethod
    def _ensure_initialized(cls):
        if cls._initialized:
            return
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            clients = db.query(ClientModel).all()
            for c in clients:
                if c.stripe_subscription_id:
                    cls._subscriptions[str(c.id)] = {
                        "client_id": str(c.id),
                        "stripe_customer_id": c.stripe_customer_id or "",
                        "stripe_subscription_id": c.stripe_subscription_id or "",
                        "package_id": c.package_id or "",
                        "status": c.subscription_status or "inactive",
                        "current_period_start": c.subscription_current_period_start.isoformat() if c.subscription_current_period_start else None,
                        "current_period_end": c.subscription_current_period_end.isoformat() if c.subscription_current_period_end else None,
                    }
            cls._initialized = True
        except Exception as e:
            logger.warning(f"Subscription store init warning: {e}")

    @classmethod
    def get_subscription(cls, client_id: str) -> Optional[Dict[str, Any]]:
        cls._ensure_initialized()
        return cls._subscriptions.get(client_id)

    @classmethod
    def set_subscription(cls, client_id: str, data: Dict[str, Any]):
        cls._ensure_initialized()
        cls._subscriptions[client_id] = data

    @classmethod
    def track_usage(cls, client_id: str, agent_id: str, task_type: str):
        cls._ensure_initialized()
        entry = {
            "id": generate_uuid(),
            "client_id": client_id,
            "agent_id": agent_id,
            "task_type": task_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        if client_id not in cls._usage:
            cls._usage[client_id] = []
        cls._usage[client_id].append(entry)
        return entry

    @classmethod
    def get_usage(cls, client_id: str, days: int = 30) -> List[Dict[str, Any]]:
        cls._ensure_initialized()
        cutoff = datetime.utcnow() - timedelta(days=days)
        usage = cls._usage.get(client_id, [])
        return [u for u in usage if datetime.fromisoformat(u["timestamp"]) > cutoff]

    @classmethod
    def add_invoice(cls, client_id: str, invoice: Dict[str, Any]):
        cls._ensure_initialized()
        if client_id not in cls._invoices:
            cls._invoices[client_id] = []
        cls._invoices[client_id].append(invoice)

    @classmethod
    def get_invoices(cls, client_id: str) -> List[Dict[str, Any]]:
        cls._ensure_initialized()
        return cls._invoices.get(client_id, [])


# ═══════════════════════════════════════════════════════════════════
# BILLING SERVICE
# ═══════════════════════════════════════════════════════════════════

class BillingService:
    """
    Complete Stripe billing integration for Claude Mythos.
    Handles subscriptions, invoices, usage tracking, and revenue metrics.
    """

    # ── Checkout ─────────────────────────────────────────────────

    async def create_checkout_session(
        self,
        client_id: str,
        package_id: str,
        success_url: str,
        cancel_url: str,
        billing_cycle: str = "monthly",
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for a new subscription.

        Args:
            client_id: Internal client ID
            package_id: 'starter', 'growth', or 'enterprise'
            success_url: Redirect URL after successful payment
            cancel_url: Redirect URL if user cancels
            billing_cycle: 'monthly' or 'annual'

        Returns:
            Dict with checkout_session_id, checkout_url, and metadata
        """
        stripe = _get_stripe()
        if not stripe:
            return {
                "error": "Stripe not configured",
                "checkout_session_id": None,
                "checkout_url": None,
            }

        package = PACKAGES.get(package_id)
        if not package:
            return {"error": f"Unknown package: {package_id}"}

        # Get or create Stripe customer
        stripe_customer_id = await self._get_or_create_customer(client_id)
        if not stripe_customer_id:
            return {"error": "Failed to create Stripe customer"}

        # Map package to Stripe Price ID
        price_id = self._get_price_id(package_id, billing_cycle)
        if not price_id:
            # Use fallback with custom line items if no price ID configured
            return await self._create_checkout_with_line_items(
                stripe_customer_id, package, package_id, success_url, cancel_url, billing_cycle
            )

        try:
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    "metadata": {
                        "client_id": client_id,
                        "package_id": package_id,
                        "package_name": package["name"],
                    },
                    "trial_period_days": 7 if package_id == "starter" else 14,
                },
                metadata={
                    "client_id": client_id,
                    "package_id": package_id,
                },
            )

            return {
                "checkout_session_id": session.id,
                "checkout_url": session.url,
                "stripe_customer_id": stripe_customer_id,
                "package_id": package_id,
                "package_name": package["name"],
                "billing_cycle": billing_cycle,
                "trial_days": 7 if package_id == "starter" else 14,
            }
        except Exception as e:
            logger.error(f"Stripe checkout error: {e}")
            return {"error": str(e)}

    async def _create_checkout_with_line_items(
        self,
        stripe_customer_id: str,
        package: Dict[str, Any],
        package_id: str,
        success_url: str,
        cancel_url: str,
        billing_cycle: str,
    ) -> Dict[str, Any]:
        """Fallback: create checkout with ad-hoc line items (no pre-configured Price ID)."""
        stripe = _get_stripe()
        if not stripe:
            return {"error": "Stripe not configured"}

        unit_amount = package["price_annual"] * 100 if billing_cycle == "annual" else package["price_monthly"] * 100

        try:
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Claude Mythos — {package['name']} ({billing_cycle.title()})",
                            "description": package["description"],
                        },
                        "unit_amount": unit_amount,
                        "recurring": {
                            "interval": "year" if billing_cycle == "annual" else "month",
                        },
                    },
                    "quantity": 1,
                }],
                mode="subscription",
                success_url=success_url,
                cancel_url=cancel_url,
                subscription_data={
                    "metadata": {
                        "client_id": "pending",
                        "package_id": package_id,
                        "package_name": package["name"],
                    },
                    "trial_period_days": 7 if package_id == "starter" else 14,
                },
            )

            return {
                "checkout_session_id": session.id,
                "checkout_url": session.url,
                "stripe_customer_id": stripe_customer_id,
                "package_id": package_id,
                "package_name": package["name"],
                "billing_cycle": billing_cycle,
                "trial_days": 7 if package_id == "starter" else 14,
                "note": "Using ad-hoc pricing — configure Stripe Price IDs for production",
            }
        except Exception as e:
            logger.error(f"Stripe checkout (fallback) error: {e}")
            return {"error": str(e)}

    # ── Webhooks ─────────────────────────────────────────────────

    async def handle_stripe_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events with signature verification.

        Args:
            payload: Raw request body bytes
            signature: Stripe-Signature header value

        Returns:
            Dict with event type and processing result
        """
        stripe = _get_stripe()
        if not stripe:
            logger.warning("Stripe not configured — webhook ignored")
            return {"status": "ignored", "reason": "stripe_not_configured"}

        # Verify webhook signature
        webhook_secret = getattr(settings, "stripe_webhook_secret", "")
        if webhook_secret:
            try:
                event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
            except stripe.error.SignatureVerificationError as e:
                logger.error(f"Stripe webhook signature verification failed: {e}")
                return {"status": "error", "reason": "signature_verification_failed"}
            except Exception as e:
                logger.error(f"Stripe webhook payload error: {e}")
                return {"status": "error", "reason": "invalid_payload"}
        else:
            # No webhook secret — parse JSON directly (development only)
            logger.warning("No STRIPE_WEBHOOK_SECRET — skipping signature verification")
            try:
                event = json.loads(payload)
            except json.JSONDecodeError as e:
                return {"status": "error", "reason": "invalid_json"}

        event_type = event.get("type", "")
        event_data = event.get("data", {}).get("object", {})

        logger.info(f"Stripe webhook received: {event_type}")

        if event_type == "checkout.session.completed":
            return await self._handle_checkout_completed(event_data)
        elif event_type == "invoice.payment_succeeded":
            return await self._handle_payment_succeeded(event_data)
        elif event_type == "invoice.payment_failed":
            return await self._handle_payment_failed(event_data)
        elif event_type == "customer.subscription.created":
            return await self._handle_subscription_created(event_data)
        elif event_type == "customer.subscription.updated":
            return await self._handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            return await self._handle_subscription_deleted(event_data)
        else:
            logger.info(f"Unhandled Stripe event type: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful checkout session completion."""
        client_id = session.get("metadata", {}).get("client_id", "")
        package_id = session.get("metadata", {}).get("package_id", "")
        subscription_id = session.get("subscription")
        customer_id = session.get("customer")

        if not client_id or not subscription_id:
            return {"status": "error", "reason": "missing_metadata"}

        # Update client record
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if client:
                client.stripe_customer_id = customer_id
                client.stripe_subscription_id = subscription_id
                client.package_id = package_id
                client.subscription_status = "active"
                db.commit()

                SubscriptionStore.set_subscription(client_id, {
                    "client_id": client_id,
                    "stripe_customer_id": customer_id,
                    "stripe_subscription_id": subscription_id,
                    "package_id": package_id,
                    "status": "active",
                    "current_period_start": datetime.utcnow().isoformat(),
                    "current_period_end": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                })
                logger.info(f"Checkout completed for client {client_id}, package {package_id}")
        except Exception as e:
            logger.error(f"Error updating client after checkout: {e}")

        return {"status": "success", "event": "checkout.session.completed", "client_id": client_id, "package_id": package_id}

    async def _handle_payment_succeeded(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful invoice payment."""
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")
        amount_paid = invoice.get("amount_paid", 0)
        period_end = invoice.get("period_end")

        # Find client by subscription
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(
                ClientModel.stripe_subscription_id == subscription_id
            ).first()
            if client:
                client.subscription_status = "active"
                if period_end:
                    client.subscription_current_period_end = datetime.utcfromtimestamp(period_end)
                db.commit()
                logger.info(f"Payment succeeded for client {client.id}, amount: {amount_paid}")
        except Exception as e:
            logger.error(f"Error handling payment success: {e}")

        return {"status": "success", "event": "invoice.payment_succeeded", "subscription_id": subscription_id}

    async def _handle_payment_failed(self, invoice: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed invoice payment."""
        subscription_id = invoice.get("subscription")
        customer_id = invoice.get("customer")

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(
                ClientModel.stripe_subscription_id == subscription_id
            ).first()
            if client:
                client.subscription_status = "past_due"
                db.commit()
                logger.warning(f"Payment failed for client {client.id}, subscription {subscription_id}")
        except Exception as e:
            logger.error(f"Error handling payment failure: {e}")

        return {"status": "success", "event": "invoice.payment_failed", "subscription_id": subscription_id}

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new subscription creation."""
        metadata = subscription.get("metadata", {})
        client_id = metadata.get("client_id", "")
        package_id = metadata.get("package_id", "")

        if client_id and client_id != "pending":
            SubscriptionStore.set_subscription(client_id, {
                "client_id": client_id,
                "stripe_customer_id": subscription.get("customer"),
                "stripe_subscription_id": subscription.get("id"),
                "package_id": package_id,
                "status": subscription.get("status", "active"),
                "current_period_start": datetime.utcfromtimestamp(
                    subscription.get("current_period_start", 0)
                ).isoformat() if subscription.get("current_period_start") else None,
                "current_period_end": datetime.utcfromtimestamp(
                    subscription.get("current_period_end", 0)
                ).isoformat() if subscription.get("current_period_end") else None,
            })

        return {"status": "success", "event": "customer.subscription.created"}

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription updates (plan changes, etc.)."""
        sub_id = subscription.get("id")
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(
                ClientModel.stripe_subscription_id == sub_id
            ).first()
            if client:
                client.subscription_status = subscription.get("status", client.subscription_status)
                db.commit()
                SubscriptionStore.set_subscription(str(client.id), {
                    "client_id": str(client.id),
                    "stripe_customer_id": subscription.get("customer"),
                    "stripe_subscription_id": sub_id,
                    "package_id": client.package_id,
                    "status": subscription.get("status", "active"),
                    "current_period_start": datetime.utcfromtimestamp(
                        subscription.get("current_period_start", 0)
                    ).isoformat() if subscription.get("current_period_start") else None,
                    "current_period_end": datetime.utcfromtimestamp(
                        subscription.get("current_period_end", 0)
                    ).isoformat() if subscription.get("current_period_end") else None,
                })
        except Exception as e:
            logger.error(f"Error handling subscription update: {e}")

        return {"status": "success", "event": "customer.subscription.updated"}

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> Dict[str, Any]:
        """Handle subscription cancellation."""
        sub_id = subscription.get("id")
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(
                ClientModel.stripe_subscription_id == sub_id
            ).first()
            if client:
                client.subscription_status = "canceled"
                db.commit()
                SubscriptionStore.set_subscription(str(client.id), {
                    "client_id": str(client.id),
                    "status": "canceled",
                })
                logger.info(f"Subscription canceled for client {client.id}")
        except Exception as e:
            logger.error(f"Error handling subscription deletion: {e}")

        return {"status": "success", "event": "customer.subscription.deleted"}

    # ── Subscription Queries ─────────────────────────────────────

    async def get_client_subscription(self, client_id: str) -> Dict[str, Any]:
        """Get subscription status for a client."""
        stripe = _get_stripe()

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client:
                return {"error": "Client not found"}

            result = {
                "client_id": client_id,
                "client_name": client.name,
                "status": client.subscription_status or "inactive",
                "package_id": client.package_id or None,
                "stripe_customer_id": client.stripe_customer_id or None,
                "stripe_subscription_id": client.stripe_subscription_id or None,
            }

            # Enrich with live Stripe data if available
            if stripe and client.stripe_subscription_id:
                try:
                    sub = stripe.Subscription.retrieve(client.stripe_subscription_id)
                    result.update({
                        "stripe_status": sub.status,
                        "current_period_start": datetime.utcfromtimestamp(sub.current_period_start).isoformat(),
                        "current_period_end": datetime.utcfromtimestamp(sub.current_period_end).isoformat(),
                        "trial_end": datetime.utcfromtimestamp(sub.trial_end).isoformat() if sub.trial_end else None,
                        "cancel_at_period_end": sub.cancel_at_period_end,
                    })
                except Exception as e:
                    logger.warning(f"Could not fetch live Stripe data: {e}")

            return result
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return {"error": str(e)}

    # ── Invoicing ────────────────────────────────────────────────

    async def create_invoice(
        self,
        client_id: str,
        items: List[Dict[str, Any]],
        description: str = "",
    ) -> Dict[str, Any]:
        """
        Create a one-off invoice for additional services.

        Args:
            client_id: Internal client ID
            items: List of {"description": str, "amount": float, "quantity": int}
            description: Invoice memo

        Returns:
            Invoice details including Stripe invoice ID
        """
        stripe = _get_stripe()
        if not stripe:
            return {"error": "Stripe not configured"}

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client or not client.stripe_customer_id:
                return {"error": "Client not found or no Stripe customer"}

            # Create invoice items
            for item in items:
                stripe.InvoiceItem.create(
                    customer=client.stripe_customer_id,
                    amount=int(item["amount"] * 100),  # cents
                    currency="usd",
                    description=item.get("description", "Service"),
                    quantity=item.get("quantity", 1),
                )

            # Create the invoice
            invoice = stripe.Invoice.create(
                customer=client.stripe_customer_id,
                description=description or f"Additional services for {client.name}",
                auto_advance=True,  # Auto-finalize and send
            )

            invoice_record = {
                "invoice_id": generate_uuid(),
                "stripe_invoice_id": invoice.id,
                "client_id": client_id,
                "items": items,
                "description": description,
                "total": sum(i["amount"] * i.get("quantity", 1) for i in items),
                "status": invoice.status,
                "created_at": datetime.utcnow().isoformat(),
            }
            SubscriptionStore.add_invoice(client_id, invoice_record)

            return {
                "status": "created",
                "invoice_id": invoice.id,
                "total": invoice_record["total"],
                "invoice_url": invoice.hosted_invoice_url,
                "pdf_url": invoice.invoice_pdf,
            }
        except Exception as e:
            logger.error(f"Error creating invoice: {e}")
            return {"error": str(e)}

    # ── Subscription Management ──────────────────────────────────

    async def cancel_subscription(self, client_id: str) -> Dict[str, Any]:
        """Cancel a client's subscription at period end."""
        stripe = _get_stripe()

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client or not client.stripe_subscription_id:
                return {"error": "No active subscription found"}

            if stripe:
                stripe.Subscription.modify(
                    client.stripe_subscription_id,
                    cancel_at_period_end=True,
                )

            client.subscription_status = "canceling"
            db.commit()

            return {
                "status": "canceling",
                "client_id": client_id,
                "message": "Subscription will cancel at the end of the current billing period",
            }
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return {"error": str(e)}

    # ── Billing Portal ───────────────────────────────────────────

    async def create_billing_portal_session(self, client_id: str, return_url: str) -> Dict[str, Any]:
        """Create a Stripe Customer Portal session for self-service billing."""
        stripe = _get_stripe()
        if not stripe:
            return {"error": "Stripe not configured"}

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client or not client.stripe_customer_id:
                return {"error": "Client not found or no Stripe customer"}

            session = stripe.billing_portal.Session.create(
                customer=client.stripe_customer_id,
                return_url=return_url,
            )

            return {
                "portal_session_id": session.id,
                "portal_url": session.url,
            }
        except Exception as e:
            logger.error(f"Error creating billing portal: {e}")
            return {"error": str(e)}

    # ── Usage Tracking ───────────────────────────────────────────

    async def track_usage(self, client_id: str, agent_id: str, task_type: str) -> Dict[str, Any]:
        """Track usage of an agent service for a client."""
        entry = SubscriptionStore.track_usage(client_id, agent_id, task_type)

        # Get campaign count for this client
        try:
            db = SessionLocal()
            from app.core.database import CampaignModel
            campaign_count = db.query(CampaignModel).filter(
                CampaignModel.client_id == client_id
            ).count()
            entry["campaign_count"] = campaign_count
        except Exception:
            pass

        return entry

    # ── Revenue Metrics ──────────────────────────────────────────

    async def get_revenue_metrics(self) -> Dict[str, Any]:
        """
        Calculate revenue metrics: MRR, ARR, churn, active subscriptions.
        """
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            clients = db.query(ClientModel).all()

            active_subscriptions = 0
            past_due = 0
            canceled = 0
            trialing = 0
            mrr = 0.0
            package_breakdown = {}

            price_map = {
                "starter": 499,
                "growth": 1499,
                "enterprise": 3999,
            }

            for client in clients:
                pkg = client.package_id or "none"
                status = client.subscription_status or "inactive"

                if status == "active":
                    active_subscriptions += 1
                    monthly = price_map.get(pkg, 0)
                    mrr += monthly
                elif status == "past_due":
                    past_due += 1
                elif status in ("canceled", "canceling"):
                    canceled += 1
                elif status == "trialing":
                    trialing += 1

                if pkg not in package_breakdown:
                    package_breakdown[pkg] = {"count": 0, "mrr": 0, "clients": []}
                package_breakdown[pkg]["count"] += 1
                if status == "active":
                    package_breakdown[pkg]["mrr"] += price_map.get(pkg, 0)

            arr = mrr * 12
            total_clients = len(clients)
            at_risk = past_due
            churn_rate = (canceled / total_clients * 100) if total_clients > 0 else 0

            return {
                "mrr": round(mrr, 2),
                "arr": round(arr, 2),
                "active_subscriptions": active_subscriptions,
                "past_due": past_due,
                "canceled_last_30d": canceled,
                "trialing": trialing,
                "total_clients": total_clients,
                "at_risk_clients": at_risk,
                "churn_rate_pct": round(churn_rate, 2),
                "avg_revenue_per_client": round(mrr / active_subscriptions, 2) if active_subscriptions > 0 else 0,
                "package_breakdown": package_breakdown,
                "projected_arr_with_expansion": round(arr * 1.15, 2),  # 15% expansion assumption
                "calculated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error calculating revenue metrics: {e}")
            return {"error": str(e)}

    # ── Monthly Invoice Generation ───────────────────────────────

    async def generate_monthly_invoices(self) -> Dict[str, Any]:
        """
        Generate invoices for any usage-based overages at month end.
        Called by scheduler on the 1st of each month.
        """
        generated = []
        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            active_clients = db.query(ClientModel).filter(
                ClientModel.subscription_status == "active"
            ).all()

            for client in active_clients:
                # Check for overages (campaigns over limit, extra agent usage)
                overages = await self._calculate_overages(str(client.id), client.package_id)
                if overages["total"] > 0:
                    invoice_result = await self.create_invoice(
                        client_id=str(client.id),
                        items=overages["items"],
                        description=f"Monthly overages for {datetime.utcnow().strftime('%B %Y')}",
                    )
                    generated.append({
                        "client_id": str(client.id),
                        "client_name": client.name,
                        "overage_total": overages["total"],
                        "invoice": invoice_result,
                    })

            return {
                "status": "complete",
                "invoices_generated": len(generated),
                "details": generated,
                "generated_at": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error generating monthly invoices: {e}")
            return {"error": str(e)}

    async def _calculate_overages(self, client_id: str, package_id: str) -> Dict[str, Any]:
        """Calculate usage overages for a client."""
        try:
            db = SessionLocal()
            from app.core.database import CampaignModel
            campaign_count = db.query(CampaignModel).filter(
                CampaignModel.client_id == client_id
            ).count()

            package = PACKAGES.get(package_id or "")
            if not package:
                return {"total": 0, "items": []}

            campaign_limit = package.get("campaigns", 0)
            if campaign_limit < 0:  # unlimited
                return {"total": 0, "items": []}

            overage_count = max(0, campaign_count - campaign_limit)
            overage_cost = overage_count * 200  # $200 per extra campaign

            if overage_count > 0:
                return {
                    "total": overage_cost,
                    "items": [{
                        "description": f"Campaign overage ({overage_count} extra campaigns)",
                        "amount": overage_cost,
                        "quantity": 1,
                    }],
                }
            return {"total": 0, "items": []}
        except Exception:
            return {"total": 0, "items": []}

    # ── Helper Methods ───────────────────────────────────────────

    async def _get_or_create_customer(self, client_id: str) -> Optional[str]:
        """Get existing Stripe customer ID or create a new one."""
        stripe = _get_stripe()
        if not stripe:
            return None

        try:
            db = SessionLocal()
            from app.core.database import ClientModel
            client = db.query(ClientModel).filter(ClientModel.id == client_id).first()
            if not client:
                return None

            # Return existing customer
            if client.stripe_customer_id:
                return client.stripe_customer_id

            # Create new Stripe customer
            customer = stripe.Customer.create(
                name=client.name,
                email=client.contact_email or None,
                phone=client.contact_phone or None,
                metadata={"client_id": client_id},
            )

            client.stripe_customer_id = customer.id
            db.commit()
            return customer.id
        except Exception as e:
            logger.error(f"Error creating Stripe customer: {e}")
            return None

    def _get_price_id(self, package_id: str, billing_cycle: str) -> Optional[str]:
        """Get Stripe Price ID for a package."""
        price_map = {
            ("starter", "monthly"): getattr(settings, "stripe_starter_price_id", ""),
            ("starter", "annual"): getattr(settings, "stripe_starter_annual_price_id", ""),
            ("growth", "monthly"): getattr(settings, "stripe_growth_price_id", ""),
            ("growth", "annual"): getattr(settings, "stripe_growth_annual_price_id", ""),
            ("enterprise", "monthly"): getattr(settings, "stripe_enterprise_price_id", ""),
            ("enterprise", "annual"): getattr(settings, "stripe_enterprise_annual_price_id", ""),
        }
        return price_map.get((package_id, billing_cycle)) or None


# ═══════════════════════════════════════════════════════════════════
# Global instance
# ═══════════════════════════════════════════════════════════════════

billing_service = BillingService()
