# WhatsApp GenAI Agent on OCI

This repo helps you set up a WhatsApp Generative AI Agent on Oracle Cloud Infrastructure (OCI) using WhatsApp Cloud API. For full step by step refer to the pdf instruction.

## Features
- WhatsApp Cloud API integration
- OCI Generative AI Agent for intelligent messaging
- Simple OCI compute setup

## Requirements
- OCI account
- Meta for Developers account
- Python ≥ 3.12

## Quick Setup
1. Create a WhatsApp Business App in [Meta for Developers](https://developers.facebook.com).
2. Configure `.env`:
```env
ACCESS_TOKEN="<token>"
APP_ID="<app id>"
APP_SECRET="<app secret>"
RECIPIENT_WAID="<phone number>"
VERSION="v22.0"
PHONE_NUMBER_ID="<phone number ID>"
VERIFY_TOKEN="<verify token>"
ENDPOINT="<OCI endpoint>"
COMPARTMENT_ID="<OCI compartment ID>"
AGENT_ENDPOINT_OCID="<OCI agent endpoint>"
```
3. Deploy webhook using OCI Starter and OCI Cloud Shell.
4. Run your app:
```bash
pip3 install -r requirements.txt
python3 run.py
```

## Testing
Use Meta’s WhatsApp sandbox for testing, then switch to verified business numbers for production.

## Troubleshooting
- Confirm Python ≥ 3.12
- Check `.env` configurations

Refer to full guide for detailed instructions.

