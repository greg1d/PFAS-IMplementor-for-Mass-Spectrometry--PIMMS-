# Reading in XML files workflow

```mermaid
graph TD
    A[Start] --> B[Do Something]
    B --> C{Decision: Is it working?}
    C -->|Yes| D[Finish]
    C -->|No| E[Fix the Issue]
    E --> B

    style A fill:#ff0000,stroke:#333,stroke-width:2px
    style B fill:#ffff00,stroke:#333,stroke-width:2px
    style C fill:#ffff00,stroke:#333,stroke-width:2px
    style D fill:#00ff00,stroke:#333,stroke-width:2px
    style E fill:#ff0000,stroke:#333,stroke-width:2px
```