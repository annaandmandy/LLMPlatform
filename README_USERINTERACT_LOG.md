Your data model centers around sessions.
Each session contains:

Session metadata

Environment details

Experiment condition

An ordered list of events (user + model + system)

```
Session
 ├── metadata
 │    ├── session_id
 │    ├── user_id (anonymized)
 │    ├── experiment_id
 │    ├── model_group / condition
 │    ├── start_time / end_time
 ├── environment
 │    ├── device_type
 │    ├── browser
 │    ├── viewport
 │    ├── connection
 └── events[]
      ├── type (click, scroll, prompt, response, etc.)
      ├── timestamp
      ├── event-specific fields

```
example:
```
{
    "session_id": { "type": "string", "description": "Unique session identifier" },
    "user_id": { "type": "string", "description": "Anonymized user identifier" },
    "experiment_id": { "type": "string", "description": "Experiment or test condition ID" },
    "model_group": { "type": "string", "description": "Assigned model group or control group" },
    "start_time": { "type": "string", "format": "date-time" },
    "end_time": { "type": "string", "format": "date-time" },
    "environment": {
      "type": "object",
      "properties": {
        "device": { "type": "string" },
        "browser": { "type": "string" },
        "os": { "type": "string" },
        "viewport": {
          "type": "object",
          "properties": {
            "width": { "type": "integer" },
            "height": { "type": "integer" }
          },
          "required": ["width", "height"]
        },
        "language": { "type": "string" },
        "connection": { "type": "string", "description": "Network type or speed estimate" }
      },
      "required": ["device", "browser"]
    },
    "events": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "t": { "type": "integer", "description": "Timestamp in ms since epoch" },
          "type": { 
            "type": "string",
            "enum": [
              "prompt", "model_response", "scroll", "click",
              "hover", "key", "navigate", "copy", "selection",
              "activity", "feedback", "error", "system"
            ]
          },
          "data": {
            "type": "object",
            "description": "Event-specific data",
            "properties": {
              "text": { "type": "string" },
              "target": { "type": "string" },
              "x": { "type": "number" },
              "y": { "type": "number" },
              "scrollY": { "type": "number" },
              "speed": { "type": "number" },
              "direction": { "type": "string", "enum": ["up", "down"] },
              "model": { "type": "string" },
              "provider": { "type": "string" },
              "latency_ms": { "type": "number" },
              "tokens": {
                "type": "object",
                "properties": {
                  "prompt": { "type": "integer" },
                  "completion": { "type": "integer" },
                  "total": { "type": "integer" }
                }
              },
              "temperature": { "type": "number" },
              "top_p": { "type": "number" },
              "response_length": { "type": "integer" },
              "response_id": { "type": "string" },
              "feedback": { "type": "string", "enum": ["up", "down", "neutral"] },
              "error_code": { "type": "string" },
              "visible_time_ms": { "type": "number" },
              "selected_text": { "type": "string" },
              "activity_state": { "type": "string", "enum": ["active", "idle"] },
              "duration_ms": { "type": "integer" }
            }
          }
        },
        "required": ["t", "type"]
      }
    }
  },
  "required": ["session_id", "user_id", "events"]
}
```