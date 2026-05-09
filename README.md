**Access Google's most capable AI models through a single MCP tool.**

A Model Context Protocol (MCP) server that exposes Google Gemini's API for generating text using state-of-the-art large language models.


## Overview

The Gemini MCP Server provides direct access to Google's Gemini LLMs:

- Generate high-quality text responses from natural language prompts
- Choose between fast and capable Gemini model variants
- Integrate Gemini's reasoning into any MCP-compatible AI workflow

Perfect for:

- AI agents that need to delegate subtasks to a powerful LLM
- Generating summaries, translations, code, or creative content
- Augmenting workflows with Gemini's reasoning and language capabilities


## Tools

<details>
<summary><code>gemini_ai_generate_text</code> — Generate text using Gemini LLM</summary>

Sends a prompt to Google Gemini and returns the generated text response.

**Inputs:**
```
- `query` (string, required) — Natural language prompt to send to Gemini
- `model` (string, optional) — Gemini model to use: gemini-2.5-flash (default) or gemini-2.5-pro
```

**Output:**

```json
{
  "prompt": "Summarize the history of the internet",
  "response": "The internet began as ARPANET in the late 1960s..."
}
```

</details>


## API Parameters Reference

<details>
<summary><strong>Available Models</strong></summary>

| Model | Description |
|---|---|
| `gemini-2.5-flash` | Fast and efficient — best for most tasks (default) |
| `gemini-2.5-pro` | More capable — best for complex reasoning and analysis |

</details>


## Getting Your Gemini API Key

<details>
<summary><strong>Steps</strong></summary>

1. Go to [Google AI Studio](https://aistudio.google.com) and sign in with your Google account
2. Navigate to **API Keys** in the left sidebar
3. Click **Create API Key**
4. Copy the generated key — you will only see it once

</details>


## Troubleshooting

<details>
<summary><strong>Missing or Invalid Headers</strong></summary>

- **Cause:** API key not provided in request headers or incorrect format
- **Solution:**
  1. Verify `Authorization: Bearer YOUR_API_KEY` and `X-Mewcp-Credential-Id: CREDENTIAL-ID` headers are present
  2. Check API key is active in your MewCP account

</details>

<details>
<summary><strong>Insufficient Credits</strong></summary>

- **Cause:** API calls have exceeded your request limits
- **Solution:**
  1. Check credit usage in your Curious Layer dashboard
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
  1. Verify endpoint format: `{server-name}/mcp/{tool-name}`
  2. Use correct server name from documentation
  3. Check available servers in your Curious Layer account

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

### Resources

- **[Google AI Studio](https://aistudio.google.com)** — Manage API keys and test Gemini models
- **[Gemini API Documentation](https://ai.google.dev/gemini-api/docs)** — Official API reference
- **[Gemini Models Overview](https://ai.google.dev/gemini-api/docs/models)** — Available models and capabilities
- **[FastMCP Docs](https://gofastmcp.com/v2/getting-started/welcome)** — FastMCP specification
- **[FastMCP Credentials](https://pypi.org/project/fastmcp-credentials/)** — FastMCP Credentials package for credential handling