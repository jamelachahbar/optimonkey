# OptiMonkey Dashboard

OptiMonkey Dashboard is an interactive web application that allows users to analyze their Azure environment for optimization opportunities using intelligent agents. The system provides recommendations to save costs on resources such as Virtual Machines, Storage Accounts, and Disks. Users can either start agents with a default prompt or choose custom prompts from predefined templates.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Getting Started](#getting-started)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Usage](#usage)
  - [Starting Agents with Default Prompt](#starting-agents-with-default-prompt)
  - [Using Prompt Cards](#using-prompt-cards)
- [License](#license)

## Overview

The OptiMonkey is built using **FastAPI** for the backend and **React** (with Chakra UI) for the frontend. The backend agents, developed using the **Autogen** library, interact with the Azure Resource Graph API and Azure Monitor to fetch and analyze usage metrics of various Azure resources.

The frontend provides a user-friendly interface where users can choose to start agents with either a default prompt or a selected custom prompt using visually appealing cards.

## Features

- Analyze Azure environment and find cost-saving opportunities.
- Utilize intelligent agents (Planner, Code Guru, Critic, User Proxy) to query Azure Resource Graph and Monitor.
- View analysis results in real-time.
- Download results as CSV files.
- Choose from predefined prompts or run with the default prompt.

## Requirements

### Backend
- **Python 3.10+**
- **FastAPI** framework
- **Autogen** library for managing agent conversations
- **Azure SDK for Python** (Azure Identity, Resource Graph, Monitor)

### Frontend
- **Typescript**
- **React** framework
- **Chakra UI** for styling

## Getting Started

### Backend Setup

1. Clone the repository and navigate to the backend folder:
   ```bash
   git clone https://github.com/jamelachahbar/optimonkey.git
   cd optimonkey/backend

2. Create a virtual environment and activate it:

    ```bash
    python3 -m venv venv
    source venv/bin/activate   
    # On Windows use 
    venv\Scripts\activate

3. Install the required Python dependencies:
    ```bash
    pip install -r requirements.txt
4. Set up the .env file for your environment variables (such as Azure credentials). You can create an .env file and populate it based on your setup. There is an example .env file.
5. Start the environment, but make sure you are in the fast api 📂
  Run the FastAPI server:
    ```bash
    uvicorn main:app --reload
 
### Frontend Setup
5. Install packages
   ```bash
    npm install
6. Start the front-end, and make sure you are in the front-end 📂 
   ```bash
   npm rum dev
   
