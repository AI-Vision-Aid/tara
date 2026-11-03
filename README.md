# Tara by Ability Bazaar

**Transaction and Request Assistant**. Tell us what you need. Tara will guide you through.

Tara is an optional voice/text concierge covering websites, apps, accessibility
testing, document remediation, free apps and the wider Ability Bazaar catalogue.
It explains verified offerings, captures requirements, reads back an editable
draft, prepares existing forms, and guides the visitor into payment checkout.

Integrated prototype: https://www.abilitybazaar.com/tara

PayPal sandbox demonstration: https://www.abilitybazaar.com/tara?demo=1

This repository is an independently runnable source package for the new Tara
layer. The `ability_tara` module, browser client, panel and catalogue match the
integrated release. The small `app.py` harness replaces the private business
platform. Its contact route is an unsent local preview. The integrated site
uses the existing real inquiry form. All Tara-assisted purchases are sandbox-only; normal marketplace checkout remains separate.

## Run locally

Python 3.11 or newer:

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Set the environment variables listed in `.env.example` in your shell or secret
manager; this app does not automatically load a .env file. Do not commit keys.
Use your own funded paid Gemini API key. Use a separate Google Cloud project
with a Firestore Native database; enable the Firestore API and run
`gcloud auth application-default login` locally. Set GOOGLE_CLOUD_PROJECT to
that project. The runtime needs permission to read/write the `tara_usage` and
`tara_demo_orders` collections. A local Firestore emulator is also supported
through FIRESTORE_EMULATOR_HOST with GOOGLE_CLOUD_PROJECT set to a test project.

For PayPal: sign in at https://developer.paypal.com/dashboard/applications/sandbox,
create/select a sandbox REST app and put its client ID and secret in the two
TARA_PAYPAL_SANDBOX variables. Create/use a separate sandbox **buyer** account
for approval. No live payment credential can substitute for a sandbox REST app.

```sh
python app.py
```

Open http://localhost:8080/tara?demo=1. Microphone use needs localhost or HTTPS
and browser permission. All features also have typed controls. The hosted demo
readiness indicator does not imply that a complete buyer capture has been tested.
If sandbox configuration is missing, the app reports that clearly and refuses
to fake a successful checkout.

## Suggested evaluation

1. Ask for a five-page bakery website, compare packages, and choose Starter.
2. Give synthetic requirements and contact details. Review the draft and edit it.
3. Read it aloud if desired, then approve the PayPal sandbox handoff.
4. Sign in with a sandbox buyer and approve. The server verifies the completed
   capture, reference, order ID, USD currency and exact catalogue amount.
5. Try cancellation, refreshing a successful callback, and an unknown question.
6. Try apps, document remediation and custom work; unknown details go to a team
   request preview. The model cannot invent a price or submit the form itself.

Use test details. Sandbox records are separate from real orders and do not
trigger fulfillment, customer messages, lead counts or revenue. PayPal approval
happens on PayPal's own domain; Tara never handles passwords or card details.
Create/capture use idempotency IDs. Pending or mismatched captures are rejected.

## AI, accessibility and limits

Google Gemini provides structured conversation; Zephyr provides female voice
with a requested neutral/slightly American delivery. Browser speech recognition
is used where available, with short-recording Gemini transcription as fallback.
Replies stream through Gemini 3.8 Flash TTS as 24 kHz PCM, with Zephyr and separate speech-style metadata. Stop, close, hiding the page and a new turn cancel queued speech. The cached welcome and complete-WAV fallback remain available. Tara uses only catalogue and public-page context, with a human-request fallback.
Keyboard controls, visible text, editable details, stop/repeat and draft readback
are included. Assistive-technology and physical-microphone testing are still
required before claiming broad accessibility validation.

Sessions are temporary process memory, not a durable CRM: one worker/instance
is required; a restart loses the active conversation. Use the shared Firestore
daily request ceiling to limit provider calls. It is not an account-wide bill cap.
Google and PayPal accounts/credits are required to run your own copy. The hosted
prototype is provided for evaluation, subject to availability and its daily limit.

## Hackathon scope and disclosure

Ability Bazaar predates the competition. Tara's conversational layer, reviewed
form handoff, price grounding, speech controls and isolated PayPal sandbox path
are new work in November 2026. Do not claim the entire marketplace was built
during this event. AI assistance from ChatGPT/Codex was used for design, coding,
debugging, documentation and validation. This source package does not constitute
a submitted hackathon entry; a real end-to-end demo video and completed sandbox
evaluation remain submission tasks. The business platform and earlier submitted
Maya/Saarthi applications remain separate.

Code is MIT licensed. Vision-Aid and Ability Bazaar names and marks identify
their owners; no endorsement by PayPal or Google is implied. Google API output
was used to create the included Zephyr welcome recording.

## Opening welcome and response timing

On Ability Bazaar, the first **Talk to Tara** activation opens the panel and
plays a prepared Zephyr welcome. It introduces accessibility testing, document
remediation, website/app development and free apps without waiting for a model
or session request. **Start voice conversation** remains the explicit microphone
action. Stop, close and page hiding cancel speech. The same page does not repeat
the welcome each time the conversation is reopened.

The standalone page attempts its welcome on arrival. If the browser blocks
autoplay, select **Start voice conversation** to hear it and begin. You can
always type instead.

The full exact service/app catalogue stays in every model request. Supporting
public-page excerpts are selected locally from packaged evidence, avoiding
runtime page rendering and repeated unrelated text. Model conversations are
stateless (`store=False`); the server continues to maintain the reviewed draft.
Prepared audio and the streaming speech format remain independently runnable.
