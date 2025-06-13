# Scout

A lightweight, AI-powered web tool to help sales teams quickly generate personalized prospect snapshots and discovery insights.

## The Problem

Sales opportunities don't always start with a scheduled meeting. They happen in hallways, at kids' soccer games, or in a chance encounter. In these moments, you need to be ready to have a smart conversation without fumbling through a CRM on your phone.

Scout is built for that moment. It's a "Conversation Engine" that provides just enough context and a few key talking points to turn a surprise meeting into a productive first touch.

## Features

* **Instant Snapshots:** Enter a prospect's name, industry, size, and region.
* **AI-Powered Insights:** Uses the OpenAI API (GPT-4o/3.5) to generate:
    * A concise summary of the company's likely context and priorities.
    * A list of conversation starters, potential objections to listen for, and a positioning statement.
* **Company Autofill:** Enter a company name and the app will make an educated guess at the industry, size, and region.
* **History:** All generated snapshots are saved in a local SQLite database for later review.
* **CRM Integration (Optional):** A simple hook is included to push the generated snapshot as a note to a HubSpot company record.

## Tech Stack

* **Backend:** Python with Flask
* **AI:** OpenAI API
* **Database:** SQLite
* **Frontend:** HTML with Tailwind CSS

## Setup

1.  Clone the repository.
2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```
3.  Set your OpenAI API key as an environment variable:
    ```bash
    export OPENAI_API_KEY="your-openai-api-key"
    ```
4.  Run the Flask application:
    ```bash
    python app.py
    ```
5.  Open your browser to `http://0.0.0.0:5012`.

