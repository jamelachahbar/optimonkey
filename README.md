
# OptiMonkey

OptiMonkey is an AI-powered platform built to optimize and manage Azure resources efficiently. Using intelligent agents, it automates FinOps (Financial Operations) tasks such as identifying unused or underutilized resources, providing cost-saving recommendations, and analyzing usage metrics across Azure subscriptions.

## Features

- **Agent-Driven FinOps**: Utilize a team of specialized agents (Planner, Code_Guru, UserProxy, Critic) to automate the analysis of Azure resources.
- **Azure Cost Optimization**: Run custom Kusto queries, extract resource IDs, and query Azure Monitor metrics to analyze underutilized resources.
- **CSV Reporting**: Automatically generate CSV reports with recommendations and usage metrics.
- **Interactive Dashboard**: A frontend interface built with React and Chakra UI to interact with the backend agents, view recommendations, and download CSV reports.
- **Customizable Queries**: Tailor Kusto queries for various Azure resource types such as Virtual Machines, Disks, and Storage Accounts.
- **Bing API Integration**: Uses Bing API for supplementary content retrieval.

## Technology Stack

### Backend
- **FastAPI**: A modern web framework for building APIs with Python.
- **Azure SDKs**: Azure Monitor, Resource Graph for querying and interacting with Azure services.
- **Autogen Framework**: Uses Autogen agents for task management, coding assistance, and resource analysis.
- **Python**: Core programming language for running the backend logic.
- **Docker**: Containerization of the application for easy deployment.

### Frontend
- **React**: Frontend framework for building the user interface.
- **Chakra UI**: A modular React component library for a better user experience.
- **PapaParse**: For parsing CSV files in the browser.
- **TypeScript**: Provides static typing for the frontend code.

## Folder Structure

```plaintext
optimonkey/
├── backend/
│   ├── fastapi-api/
│   │   ├── agents/
│   │   │   ├── OAI_CONFIG_LIST.json
│   │   │   ├── optimonkeyagents.py
│   │   ├── main.py
│   │   ├── routers/
│   ├── flask-api/
│   ├── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Insights.tsx
│   ├── public/
├── Dockerfile
├── .env
```

### Backend Directory
- **agents/**: Contains agent-related logic for analyzing Azure resources.
- **routers/**: API endpoints for starting agent conversations and fetching recommendations.
- **main.py**: Entry point for the FastAPI backend.
- **requirements.txt**: Lists dependencies for the backend.

### Frontend Directory
- **components/**: Contains React components such as `Dashboard.tsx` for rendering the interactive UI.
- **api/**: Interfaces with the backend API to start agents and fetch recommendations.
- **public/**: Static assets for the frontend.

## Getting Started

### Prerequisites

- **Azure Subscription**: To run the application, you’ll need an Azure subscription.
- **Bing API Key**: Obtain a Bing API key for the document retrieval functionality.
- **Docker**: Ensure you have Docker installed for containerization.

### Environment Variables

Create a `.env` file in the backend directory with the following variables:

```bash
BING_API_KEY=your_bing_api_key_here
```

### Installation

1. **Clone the repository**:

   ```bash
   git clone https://github.com/yourusername/optimonkey.git
   cd optimonkey
   ```

2. **Backend Setup**:

   - Install Python dependencies:

     ```bash
     pip install -r backend/requirements.txt
     ```

   - Start the FastAPI backend:

     ```bash
     cd backend/fastapi-api
     uvicorn main:app --reload
     ```

3. **Frontend Setup**:

   - Navigate to the frontend directory and install dependencies:

     ```bash
     cd frontend
     npm install
     ```

   - Start the React development server:

     ```bash
     npm start
     ```

4. **Running with Docker**:

   To run both the backend and frontend in Docker containers, build the images and run the containers:

   ```bash
   docker-compose up --build
   ```

### Usage

1. **Start Agents**: Click the "Start Agents" button to initiate the agents' conversation and begin the analysis.
2. **Fetch Recommendations**: Click "Show Recommendations" to fetch cost-saving recommendations for Azure resources.
3. **Download CSV**: After fetching recommendations, you can download the CSV report.

### API Endpoints

- **/start-agents**: POST request to start agent conversations and perform resource analysis.
- **/download-recommendations**: GET request to download the CSV file with cost-saving recommendations.

## Troubleshooting

- Ensure your Azure credentials are correctly configured (e.g., using `AzureCliCredential` for authentication).
- If you encounter issues with the Bing API, verify that your API key is valid and set correctly in the `.env` file.

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/your-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/your-feature`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License.
