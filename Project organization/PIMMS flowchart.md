# Reading in XML files workflow

```mermaid
graph TD
    A[Start] --> B[Do Something]
    B --> C{Decision: Is it working?}
    C -->|Yes| D[Finish]
    C -->|No| E[Fix the Issue]
    E --> B
```