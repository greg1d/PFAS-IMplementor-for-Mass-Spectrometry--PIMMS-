# Reading in XML files workflow

```mermaid
graph TD
    A[Profiler steps<br><ol><li>Import files to Agilent MassHunter Mass Profiler</li><li>File>Export Each Sample to CEF...</li><li>Select no on choosing averaged values across all samples</li></ol>] --> B[Browse and add individual files into the File Hub in PIMMS] --> C[Move files you wish to analyze over to the Processing Hub using the arrows] --> D[Hit convert to feather file to read in the sample files]

    style A fill:#A2AAAD,stroke:#333,stroke-width:2px,color:#000000,font-weight:bold
    style B fill:#A2AAAD,stroke:#333,stroke-width:2px,color:#000000,font-weight:bold
    style C fill:#A2AAAD,stroke:#333,stroke-width:2px,color:#000000,font-weight:bold
    style D fill:#A2AAAD,stroke:#333,stroke-width:2px,color:#000000,font-weight:bold

    subgraph someID[Importing CEFs]
        direction LR
        D ~~~ E[If you try to process a file and PIMMS already has a copy loaded into it's database, it will not reprocess the file.
        If you modify or edit the .CEF file you are importing e.g. changing the title, editing the file location, changing the contents of the file in anyway PIMMS will reprocess that file when loaded into the processing hub to make sure it has the most up-to-date version of your data]
    end

    style E fill:#FFD700,stroke:#333,stroke-width:2px,color:#000000,shape:circle, font-size: 10pt
    linkStyle 0 opacity:0;
