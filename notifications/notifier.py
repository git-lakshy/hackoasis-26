"""
Notification module: Slack (rich blocks + action buttons), Email, and Twilio SMS.
"""
import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request, error
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL = os.getenv("SLACK_CHANNEL", "#finops-alerts")
DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:8501")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")  # e.g. +15551234567
TWILIO_TO = os.getenv("TWILIO_TO_NUMBER")       # your phone number


# ── Internal helpers ──────────────────────────────────────────────────────────

def _post_slack(payload: dict):
    if not SLACK_WEBHOOK_URL:
        return
    data = json.dumps(payload).encode()
    req = request.Request(
        SLACK_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        request.urlopen(req, timeout=10)
    except error.URLError:
        pass


def _send_sms(body: str):
    """Send SMS via Twilio REST API (no SDK needed)."""
    if not all([TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM, TWILIO_TO]):
        return
    import base64
    from urllib.parse import urlencode

    url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
    credentials = base64.b64encode(f"{TWILIO_ACCOUNT_SID}:{TWILIO_AUTH_TOKEN}".encode()).decode()
    data = urlencode({"From": TWILIO_FROM, "To": TWILIO_TO, "Body": body}).encode()
    req = request.Request(url, data=data, headers={
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    })
    try:
        request.urlopen(req, timeout=10)
    except Exception:
        pass


# ── Notifier classes ──────────────────────────────────────────────────────────

class SlackNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        resource_id = opp_dict.get("resource_id", "unknown")
        action = opp_dict.get("action", "unknown")
        risk_tier = risk_dict.get("risk_tier", "unknown")
        savings = opp_dict.get("projected_savings", 0)
        confidence = sim_dict.get("confidence", 0)
        score = tradeoff_dict.get("composite_score", 0)
        risk_factors = ", ".join(risk_dict.get("risk_factors", []))

        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_tier, "⚪")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚠️ Baburao FinOps: Approval Required", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Resource*\n`{resource_id}`"},
                    {"type": "mrkdwn", "text": f"*Action*\n`{action}`"},
                    {"type": "mrkdwn", "text": f"*Risk Tier*\n{risk_emoji} `{risk_tier}`"},
                    {"type": "mrkdwn", "text": f"*Projected Savings*\n`${savings:,.2f}/mo`"},
                    {"type": "mrkdwn", "text": f"*Confidence*\n`{confidence:.0%}`"},
                    {"type": "mrkdwn", "text": f"*Composite Score*\n`{score:.2f}`"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Risk Factors:* {risk_factors or 'None'}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve", "emoji": True},
                        "style": "primary",
                        "value": f"approve:{resource_id}",
                        "action_id": "approve_action",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject", "emoji": True},
                        "style": "danger",
                        "value": f"reject:{resource_id}",
                        "action_id": "reject_action",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Dashboard", "emoji": True},
                        "url": DASHBOARD_URL,
                        "action_id": "view_dashboard",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🤖 *Baburao* — Intelligent Infrastructure Cost Optimizer"}
                ],
            },
        ]
        _post_slack({"blocks": blocks})

    def send_execution_summary(self, executed: list, total_savings: float):
        if not executed:
            return
        rows = "\n".join(
            f"• `{r.get('resource_id')}` — {r.get('action')} → *${r.get('actual_savings', 0):,.0f}/mo*"
            for r in executed[:10]
        )
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✅ Baburao: Optimizations Executed", "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{len(executed)} actions executed — Total savings: ${total_savings:,.0f}/mo*\n\n{rows}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Dashboard", "emoji": True},
                        "url": DASHBOARD_URL,
                    }
                ],
            },
        ]
        _post_slack({"blocks": blocks})

    def send_alert(self, title: str, message: str, level: str = "info"):
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}.get(level, "ℹ️")
        _post_slack({
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{emoji} *{title}*\n{message}"},
                }
            ]
        })


class TwilioNotifier:
    def send_approval_sms(self, resource_id: str, action: str, risk_tier: str, savings: float):
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_tier, "⚪")
        msg = (
            f"🤖 Baburao FinOps Alert\n"
            f"{risk_emoji} Approval Required\n"
            f"Resource: {resource_id}\n"
            f"Action: {action} | Risk: {risk_tier}\n"
            f"Saves: ${savings:,.0f}/mo\n"
            f"Run: baburao approve"
        )
        _send_sms(msg)

    def send_execution_sms(self, count: int, total_savings: float):
        msg = (
            f"✅ Baburao: {count} optimization(s) executed.\n"
            f"Total savings: ${total_savings:,.0f}/mo"
        )
        _send_sms(msg)


class EmailNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        if not NOTIFY_EMAIL:
            return
        resource_id = opp_dict.get("resource_id", "unknown")
        html = f"""
        <html><body style="font-family:sans-serif">
        <h2>⚠️ Approval Required — Baburao FinOps AI</h2>
        <table border="1" cellpadding="8" cellspacing="0">
          <tr><td><b>Resource ID</b></td><td>{resource_id}</td></tr>
          <tr><td><b>Action</b></td><td>{opp_dict.get('action')}</td></tr>
          <tr><td><b>Risk Tier</b></td><td>{risk_dict.get('risk_tier')}</td></tr>
          <tr><td><b>Risk Factors</b></td><td>{', '.join(risk_dict.get('risk_factors', []))}</td></tr>
          <tr><td><b>Projected Savings</b></td><td>${opp_dict.get('projected_savings', 0):.2f}/mo</td></tr>
          <tr><td><b>Confidence</b></td><td>{sim_dict.get('confidence', 0):.0%}</td></tr>
          <tr><td><b>Composite Score</b></td><td>{tradeoff_dict.get('composite_score', 0):.2f}</td></tr>
        </table>
        <p><a href="{DASHBOARD_URL}">View Dashboard</a></p>
        </body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Baburao FinOps] Approval Required: {resource_id}"
        msg["From"] = SMTP_USER or "noreply@finops"
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(msg["From"], NOTIFY_EMAIL, msg.as_string())
        except Exception:
            pass


# ── Public API ────────────────────────────────────────────────────────────────

def notify_approval_required(opp_dict, risk_dict, sim_dict, tradeoff_dict):
    SlackNotifier().send(opp_dict, risk_dict, sim_dict, tradeoff_dict)
    EmailNotifier().send(opp_dict, risk_dict, sim_dict, tradeoff_dict)
    TwilioNotifier().send_approval_sms(
        opp_dict.get("resource_id", "unknown"),
        opp_dict.get("action", "unknown"),
        risk_dict.get("risk_tier", "unknown"),
        opp_dict.get("projected_savings", 0),
    )


def notify_execution_summary(executed: list):
    total = sum(r.get("actual_savings", 0) for r in executed)
    SlackNotifier().send_execution_summary(executed, total)
    TwilioNotifier().send_execution_sms(len(executed), total)



def _post_slack(payload: dict):
    if not SLACK_WEBHOOK_URL:
        return
    data = json.dumps(payload).encode()
    req = request.Request(
        SLACK_WEBHOOK_URL,
        data=data,
        headers={"Content-Type": "application/json"},
    )
    try:
        request.urlopen(req, timeout=10)
    except error.URLError:
        pass


class SlackNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        resource_id = opp_dict.get("resource_id", "unknown")
        action = opp_dict.get("action", "unknown")
        risk_tier = risk_dict.get("risk_tier", "unknown")
        savings = opp_dict.get("projected_savings", 0)
        confidence = sim_dict.get("confidence", 0)
        score = tradeoff_dict.get("composite_score", 0)
        risk_factors = ", ".join(risk_dict.get("risk_factors", []))

        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}.get(risk_tier, "⚪")

        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "⚠️ FinOps: Approval Required", "emoji": True},
            },
            {"type": "divider"},
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Resource*\n`{resource_id}`"},
                    {"type": "mrkdwn", "text": f"*Action*\n`{action}`"},
                    {"type": "mrkdwn", "text": f"*Risk Tier*\n{risk_emoji} `{risk_tier}`"},
                    {"type": "mrkdwn", "text": f"*Projected Savings*\n`${savings:,.2f}/mo`"},
                    {"type": "mrkdwn", "text": f"*Confidence*\n`{confidence:.0%}`"},
                    {"type": "mrkdwn", "text": f"*Composite Score*\n`{score:.2f}`"},
                ],
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Risk Factors:* {risk_factors or 'None'}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve", "emoji": True},
                        "style": "primary",
                        "value": f"approve:{resource_id}",
                        "action_id": "approve_action",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject", "emoji": True},
                        "style": "danger",
                        "value": f"reject:{resource_id}",
                        "action_id": "reject_action",
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Dashboard", "emoji": True},
                        "url": DASHBOARD_URL,
                        "action_id": "view_dashboard",
                    },
                ],
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "🤖 *Baburao* — Intelligent Infrastructure Cost Optimizer"}
                ],
            },
        ]
        _post_slack({"blocks": blocks})

    def send_execution_summary(self, executed: list, total_savings: float):
        """Send a summary after optimizations are executed."""
        if not executed:
            return
        rows = "\n".join(
            f"• `{r.get('resource_id')}` — {r.get('action')} → *${r.get('actual_savings', 0):,.0f}/mo*"
            for r in executed[:10]
        )
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "✅ Optimizations Executed", "emoji": True},
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{len(executed)} actions executed — Total savings: ${total_savings:,.0f}/mo*\n\n{rows}"},
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "📊 View Dashboard", "emoji": True},
                        "url": DASHBOARD_URL,
                    }
                ],
            },
        ]
        _post_slack({"blocks": blocks})

    def send_alert(self, title: str, message: str, level: str = "info"):
        """Generic alert (info/warning/error)."""
        emoji = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}.get(level, "ℹ️")
        _post_slack({
            "blocks": [
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": f"{emoji} *{title}*\n{message}"},
                }
            ]
        })


class EmailNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        if not NOTIFY_EMAIL:
            return
        resource_id = opp_dict.get("resource_id", "unknown")
        html = f"""
        <html><body style="font-family:sans-serif">
        <h2>⚠️ Approval Required — FinOps AI Agent</h2>
        <table border="1" cellpadding="8" cellspacing="0">
          <tr><td><b>Resource ID</b></td><td>{resource_id}</td></tr>
          <tr><td><b>Action</b></td><td>{opp_dict.get('action')}</td></tr>
          <tr><td><b>Risk Tier</b></td><td>{risk_dict.get('risk_tier')}</td></tr>
          <tr><td><b>Risk Factors</b></td><td>{', '.join(risk_dict.get('risk_factors', []))}</td></tr>
          <tr><td><b>Projected Savings</b></td><td>${opp_dict.get('projected_savings', 0):.2f}/mo</td></tr>
          <tr><td><b>Confidence</b></td><td>{sim_dict.get('confidence', 0):.0%}</td></tr>
          <tr><td><b>Composite Score</b></td><td>{tradeoff_dict.get('composite_score', 0):.2f}</td></tr>
        </table>
        <p><a href="{DASHBOARD_URL}">View Dashboard</a></p>
        </body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[FinOps] Approval Required: {resource_id}"
        msg["From"] = SMTP_USER or "noreply@finops"
        msg["To"] = NOTIFY_EMAIL
        msg.attach(MIMEText(html, "html"))
        try:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.ehlo()
                server.starttls()
                if SMTP_USER and SMTP_PASS:
                    server.login(SMTP_USER, SMTP_PASS)
                server.sendmail(msg["From"], NOTIFY_EMAIL, msg.as_string())
        except Exception:
            pass


def notify_approval_required(opp_dict, risk_dict, sim_dict, tradeoff_dict):
    SlackNotifier().send(opp_dict, risk_dict, sim_dict, tradeoff_dict)
    EmailNotifier().send(opp_dict, risk_dict, sim_dict, tradeoff_dict)


def notify_execution_summary(executed: list):
    total = sum(r.get("actual_savings", 0) for r in executed)
    SlackNotifier().send_execution_summary(executed, total)
