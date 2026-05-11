**Access Google's most capable AI models through a single MCP tool.**

A Model Context Protocol (MCP) server that exposes Google Gemini's API for generating text using state-of-the-art large language models.

---

## Overview

The Gemini MCP Server provides direct access to Google's Gemini LLMs:

- Generate high-quality text responses from natural language prompts
- Choose between fast and capable Gemini model variants
- Integrate Gemini's reasoning into any MCP-compatible AI workflow

Perfect for:

- AI agents that need to delegate subtasks to a powerful LLM
- Generating summaries, translations, code, or creative content
- Augmenting workflows with Gemini's reasoning and language capabilities

---

## Tools

<details>
<summary><code>gemini_ai_generate_text</code> — Generate text using Gemini LLM</summary>

Sends a prompt to Google Gemini and returns the generated text response.

**Inputs:**

- `query` (string, required) — Natural language prompt to send to Gemini
- `model` (string, optional) — Gemini model to use: `gemini-2.5-flash` (default) or `gemini-2.5-pro`

**Output:**

```json
{
  "prompt": "Summarize the history of the internet",
  "response": "The internet began as ARPANET in the late 1960s..."
}
```

**Usage Example:**

```bash
POST /mcp/gemini/gemini_ai_generate_text

{
  "query": "Summarize the history of the internet",
  "model": "gemini-2.5-flash"
}
```

</details>

---

<details>
<summary><strong>API Parameters Reference</strong></summary>

### Available Models

| Model | Description |
|---|---|
| `gemini-2.5-flash` | Fast and efficient — best for most tasks (default) |
| `gemini-2.5-pro` | More capable — best for complex reasoning and analysis |

</details>

---

<details>
<summary><strong>Authentication Setup</strong></summary>

All tools authenticate via a Gemini API key stored in MewCP credentials. Here's the full setup:

### Step 1: Get Your Gemini API Key

1. Go to [Google AI Studio API Keys](https://aistudio.google.com/app/apikey)
2. Sign in with your Google account
3. Click **Create API Key**
4. Select or create a Google Cloud project to associate with the key
5. Copy the generated key — store it securely, you will only see it once

Refer to the [Gemini API Key documentation](https://ai.google.dev/gemini-api/docs/api-key) for details.

### Step 2: Add the Key to MewCP

1. Go to your MewCP dashboard → **Credentials**
2. Click **Add Credential** and select **Gemini**
3. Paste your Gemini API key in the **API Key** field
4. Save — note the credential ID assigned to it

### Step 3: Authenticate Your Requests

Include both headers in every request to the MewCP gateway:

```http
Authorization: Bearer <YOUR_MEWCP_API_KEY>
X-Mewcp-Credential-Id: <YOUR_CREDENTIAL_ID>
```

The gateway resolves the stored Gemini API key from the credential ID and injects it into the server transparently — your Gemini key never travels in the request body.

</details>

---

## Troubleshooting

<details>
<summary><strong>Missing or Invalid API Key</strong></summary>

- **Cause:** MewCP authentication headers are missing or the credential is invalid
- **Solution:**
  1. Verify both headers are present in your request:
     ```http
     Authorization: Bearer <YOUR_MEWCP_API_KEY>
     X-Mewcp-Credential-Id: <YOUR_CREDENTIAL_ID>
     ```
  2. Check your MewCP API key is valid in your MewCP account
  3. Confirm the credential ID corresponds to a saved Gemini credential

</details>

<details>
<summary><strong>Insufficient Credits</strong></summary>

- **Cause:** API calls have exceeded your request limits
- **Solution:**
  1. Check usage limits in your MewCP dashboard
  2. Upgrade to a paid plan or add credits for higher limits
  3. Contact support for credit adjustments

</details>

<details>
<summary><strong>Credential Not Connected</strong></summary>

- **Cause:** No Gemini API key linked to your account
- **Solution:**
  1. Go to **Credentials** in your MewCP dashboard
  2. Add your Google Gemini API key
  3. Retry the request with the correct `X-Mewcp-Credential-Id` header

</details>

<details>
<summary><strong>Malformed Request Payload</strong></summary>

- **Cause:** JSON payload is invalid or missing required fields
- **Solution:**
  1. Validate JSON syntax before sending
  2. Ensure the `query` parameter is included and non-empty
  3. Check the `model` value matches one of the supported model names

</details>

<details>
<summary><strong>Server Not Found</strong></summary>

- **Cause:** Incorrect server name in the API endpoint
- **Solution:**
  1. Verify endpoint format: `/mcp/{server-name}/{tool-name}`
  2. Use correct server name from documentation
  3. Check available servers in your MewCP account

</details>

<details>
<summary><strong>Gemini API Error</strong></summary>

- **Cause:** Upstream Google Gemini API returned an error
- **Solution:**
  1. Check Google Cloud status at [Google Status](https://status.cloud.google.com)
  2. Verify your API key has access to the Gemini API and the selected model
  3. Review the error message returned in the response for specific details

</details>

---

<details>
<summary><strong>Resources</strong></summary>

- **[Google AI Studio](https://aistudio.google.com)** — Manage API keys and test Gemini models
- **[Gemini API Documentation](https://ai.google.dev/gemini-api/docs)** — Official API reference
- **[Gemini Models Overview](https://ai.google.dev/gemini-api/docs/models)** — Available models and capabilities
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[fastmcp-credentials package](https://github.com/AStheTECH/fastmcp-credentials)** — FastMCP Credentials specification

</details>
