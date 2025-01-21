## Roadmap

Building a website requires a number of upfront decisions with the additional complexity that these decisions can impact other components.  With this undertaking there we making ways we can choose to build up the website.  In this document I'm going to outline what we intent to build and how these dependencies are interrelated.

### Minimum Viable Product

Often shortened to MVP, the purpose of an MVP is to expose enough functionality that it can be shown to stakeholders and customers to get feedback to inform future decisions and product direction.  I'm focusing on two possible definitions for this effort, a read-only monitor that enhances the existing CLI experience vs a smaller functional surface for setup, snapshot, metadata and backfill migration.

#### Migration Monitor

This experience keeps the CLI for Migration Assistant prominently featured, all create/update/delete actions will still be done through the CLI interface, such as `console snapshot create`.  This experience will focus on replacing the use of commands such as `console snapshot status`.

##### Positives
- All customers of Migration Assistant will benefit from the visualizations
- Easier to implement APIs only supporting the `R` from `CRUD`.
- Opportunity to add CLI documentation/reference

##### Negatives  
- Configuration of MA is a getting started pain-point 
- Over-index on more complex visualizations such as the capture/replay tuples

#### Migration Assistant Backfill *Recommended*

##### Positives
- Create an end to end demo that sets up expectations for the full MA UX.
- Better vet API workflow with full range of commands
- Customer will be able to complete a migration
- Incomplete migrations become fast follow-up for iteration

##### Negatives  
- Replayer scenarios will wait longer before seeing investment