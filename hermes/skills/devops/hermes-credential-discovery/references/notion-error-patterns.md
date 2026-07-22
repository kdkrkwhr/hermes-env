# Notion API Error Patterns

## 404 "Could not find page" — Integration not shared

Full error shape:

```json
{
  "object": "error",
  "status": 404,
  "code": "object_not_found",
  "message": "Could not find page with ID: 39d02551-8b5c-8095-844a-c8d55b10eff9. Make sure the relevant pages and databases are shared with your integration \"task_automation\".",
  "additional_data": {
    "integration_id": "34202551-8b5c-8165-a07e-00272141838a"
  }
}
```

Key extraction: the `message` field names the integration (`"task_automation"` in this example). This is the exact name the user needs to find in Notion's `···` → `Connections` → `Connect to` menu.

## Diagnosing token vs. permission issues

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| 401 Unauthorized | Bad/missing token | Check `NOTION_API_KEY` value, bearer header |
| 404 with integration name in message | Page not shared | Share page with integration in Notion UI |
| 404 without integration name | Wrong page ID or page doesn't exist | Verify UUID from URL |
| 200 but empty markdown | Page has no content / is a database | Use `/data_sources/{id}/query` for DBs |

## URL → Page ID extraction

Notion URLs follow this pattern:
```
https://app.notion.com/p/AllRe3-0-Engine-API-39d025518b5c8095844ac8d55b10eff9
```

The page ID is the last 32 hex chars: `39d025518b5c8095844ac8d55b10eff9`. Notion API accepts both dashed and undashed UUIDs.
