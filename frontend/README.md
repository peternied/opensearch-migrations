
## Migration Assistant Frontend
This project contains all the frontend components for the Migration Assistant.  Deployed alongside the Migration Assistant, this website provide a graphical user interface to customers so they can monitor, update, and complete a migration. 

- [Migration Assistant Frontend](#migration-assistant-frontend)
- [Start the Frontend](#start-the-frontend)
- [Deployment](#deployment)
- [Configuration](#configuration)

## Start the Frontend

Run the development server:

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

## Deployment

> !Note
> Not yet available for deployment

In production scenarios the frontend is deployed with the same process as the Migration Console.  By using the [Solutions Deployment](../deployment/migration-assistant-solution/README.md) it will be deployed to the AWS Cloud.


## Configuration

To communicate with the backend systems the endpoint needs to be known before starting the development server, it is set through the environment variable

```bash
set MA_CONSOLE_API_URL=https://localhost:8000
```