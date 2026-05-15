import json
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib import request, error
from dotenv import load_dotenv

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")


class SlackNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        if not SLACK_WEBHOOK_URL:
            return
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Approval Required* — Resource: `{opp_dict.get('resource_id')}`\n"
                        f"*Action:* {opp_dict.get('action')} | *Risk Tier:* {risk_dict.get('risk_tier')}\n"
                        f"*Risk Factors:* {', '.join(risk_dict.get('risk_factors', []))}\n"
                        f"*Projected Savings:* ${opp_dict.get('projected_savings', 0):.2f} | "
                        f"*Confidence:* {sim_dict.get('confidence', 0):.0%} | "
                        f"*Composite Score:* {tradeoff_dict.get('composite_score', 0):.2f}\n"
                        f"<http://localhost:8501|View Dashboard>"
                    ),
                },
            }
        ]
        payload = json.dumps({"blocks": blocks}).encode()
        req = request.Request(
            SLACK_WEBHOOK_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            request.urlopen(req, timeout=10)
        except error.URLError:
            pass


class EmailNotifier:
    def send(self, opp_dict, risk_dict, sim_dict, tradeoff_dict):
        if not NOTIFY_EMAIL:
            return
        html = f"""
        <html><body>
        <h2>Approval Required</h2>
        <table>
          <tr><td><b>Resource ID</b></td><td>{opp_dict.get('resource_id')}</td></tr>
          <tr><td><b>Action</b></td><td>{opp_dict.get('action')}</td></tr>
          <tr><td><b>Risk Tier</b></td><td>{risk_dict.get('risk_tier')}</td></tr>
          <tr><td><b>Risk Factors</b></td><td>{', '.join(risk_dict.get('risk_factors', []))}</td></tr>
          <tr><td><b>Projected Savings</b></td><td>${opp_dict.get('projected_savings', 0):.2f}</td></tr>
          <tr><td><b>Confidence</b></td><td>{sim_dict.get('confidence', 0):.0%}</td></tr>
          <tr><td><b>Composite Score</b></td><td>{tradeoff_dict.get('composite_score', 0):.2f}</td></tr>
        </table>
        <p><a href="http://localhost:8501">View Dashboard</a></p>
        </body></html>
        """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[Cost Optimizer] Approval Required: {opp_dict.get('resource_id')}"
        msg["From"] = SMTP_USER or "noreply@costoptimizer"
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
