<a id="readme-top"></a>

<!-- PROJECT SHIELDS -->
[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]



<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/giusber2005/chargeBot">
    <img src="static/images/HappyFace-Transparent.png" alt="Logo" width="80" height="80">
  </a>

<h3 align="center">ChargeBot</h3>

  <p align="center">
    An AI assistant for EV charging stations that suggests what to do nearby while your car charges.
    <br />
    <a href="https://chargebot-2x2k.onrender.com">View Demo</a>
    &middot;
    <a href="https://github.com/giusber2005/chargeBot/issues/new?labels=bug">Report Bug</a>
    &middot;
    <a href="https://github.com/giusber2005/chargeBot/issues/new?labels=enhancement">Request Feature</a>
  </p>
</div>



<!-- TABLE OF CONTENTS -->
<details>
  <summary>Table of Contents</summary>
  <ol>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
        <li><a href="#built-with">Built With</a></li>
      </ul>
    </li>
    <li>
      <a href="#getting-started">Getting Started</a>
      <ul>
        <li><a href="#prerequisites">Prerequisites</a></li>
        <li><a href="#installation">Installation</a></li>
      </ul>
    </li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#architecture">Architecture</a></li>
    <li><a href="#roadmap">Roadmap</a></li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>



<!-- ABOUT THE PROJECT -->
## About The Project

ChargeBot is a web app meant to run on the screen of an electric vehicle charging station. While the car charges, the driver can chat with a bot that suggests events, activities and points of interest nearby that fit the time left, the weather and their preferences.

* **Chat assistant**: an OpenAI GPT-4o bot answers using Retrieval-Augmented Generation over fresh data from the [Open Data Hub](https://opendatahub.it) (events of the day, seasonal activities, 3-hour weather forecast, distance from the charger to each point of interest). Voice messages are transcribed with Whisper.
* **Charging dashboard**: next to the chat, a simulated DC fast-charging session (77 kWh battery on a 150 kW CCS2 charger) shows state of charge, time to the 80% target, power curve, energy delivered, cost, range added, voltage, current and battery temperature. The bot knows the remaining time, so its suggestions fit the wait.
* **Demo mode**: a toggle that answers straight from the Open Data Hub data without calling the AI, so the app can be explored without API credits. Without an API key the app always runs in demo mode.
* **Mobile ready**: the interface works on phones as well as on the station screen.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

* [![Python][Python]][Python-url]
* [![Flask][Flask]][Flask-url]
* [![OpenAI][OpenAI]][OpenAI-url]
* [![SQLite][SQLite]][SQLite-url]
* [![JavaScript][JavaScript]][JavaScript-url]
* [![Docker][Docker]][Docker-url]

Other libraries: Flask-Session, APScheduler, Gunicorn, Requests, python-dotenv.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- GETTING STARTED -->
## Getting Started

If you only want to try ChargeBot, open the [live demo](https://chargebot-2x2k.onrender.com). To run it locally, follow these steps.

### Prerequisites

* [Docker](https://docs.docker.com/get-docker/) with Docker Compose
* An [OpenAI API key](https://platform.openai.com/api-keys) (optional, without it the app runs in demo mode)

### Installation

1. Clone the repo
   ```sh
   git clone https://github.com/giusber2005/chargeBot.git
   cd chargeBot
   ```
2. Create a `.env` file in the project root
   ```env
   SECRET_KEY=any-long-random-string
   CHATGPT_API_KEY=sk-...
   # Optional
   OPENAI_MODEL=gpt-4o
   CHARGING_PRICE_PER_KWH=0.59
   CHARGING_TIME_SCALE=1
   ```
   `CHARGING_TIME_SCALE` speeds up the simulated charging session (e.g. `20` makes it 20 times faster).
3. Start the app
   ```sh
   docker compose up
   ```
4. Open <http://localhost:5000>

To stop it, run `docker compose down -v --remove-orphans`.

<details>
  <summary>Without Docker</summary>

  ```sh
  python3 -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  python app.py
  ```
  When running without Docker, the API key can also be set as `OPENAI_API_KEY`.
</details>

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## Usage

* Start a conversation and tell the bot what you like (food, culture, sport, a walk...). It replies with suggestions that fit the remaining charging time.
* Keep chatting to refine the results: the conversation keeps its context.
* Use the **Demo mode** switch in the top right corner to browse activities without calling the AI.
* Stop and restart the charging session from the dashboard.

The data is refreshed at the first prompt of the day. Conversations are stored in a SQLite database and old records are cleared every hour.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ARCHITECTURE -->
## Architecture

![Architecture][architecture]

The app loads the weather forecast, seasonal activities, daily events and the distance between the charging station and each point of interest from the Open Data Hub, stores them in a dataset and uses it for RAG with GPT-4o. The prompts keep the model on topic and limit hallucinations, while still answering off-topic questions politely and briefly.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ROADMAP -->
## Roadmap

- [x] RAG over Open Data Hub data
- [x] Demo mode without API key
- [x] Simulated charging dashboard
- [ ] Connect the dashboard to a real charging station
- [ ] Use stored conversations to personalise suggestions

See the [open issues](https://github.com/giusber2005/chargeBot/issues) for a full list of proposed features (and known issues).

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are welcome. If you have a suggestion, fork the repo and open a pull request, or open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>

### Top contributors:

<a href="https://github.com/giusber2005/chargeBot/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=giusber2005/chargeBot" alt="contrib.rocks image" />
</a>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## Contact

Giuseppe Berardi - [@giusber2005](https://github.com/giusber2005)

Project Link: [https://github.com/giusber2005/chargeBot](https://github.com/giusber2005/chargeBot)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Open Data Hub](https://opendatahub.it) for the tourism, events and weather data
* [OpenAI](https://openai.com)
* [Best-README-Template](https://github.com/othneildrew/Best-README-Template)

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- MARKDOWN LINKS & IMAGES -->
[contributors-shield]: https://img.shields.io/github/contributors/giusber2005/chargeBot.svg?style=for-the-badge
[contributors-url]: https://github.com/giusber2005/chargeBot/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/giusber2005/chargeBot.svg?style=for-the-badge
[forks-url]: https://github.com/giusber2005/chargeBot/network/members
[stars-shield]: https://img.shields.io/github/stars/giusber2005/chargeBot.svg?style=for-the-badge
[stars-url]: https://github.com/giusber2005/chargeBot/stargazers
[issues-shield]: https://img.shields.io/github/issues/giusber2005/chargeBot.svg?style=for-the-badge
[issues-url]: https://github.com/giusber2005/chargeBot/issues
[license-shield]: https://img.shields.io/github/license/giusber2005/chargeBot.svg?style=for-the-badge
[license-url]: https://github.com/giusber2005/chargeBot/blob/main/LICENSE
[architecture]: static/images/Architecture.jpg
[Python]: https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://www.python.org/
[Flask]: https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white
[Flask-url]: https://flask.palletsprojects.com/
[OpenAI]: https://img.shields.io/badge/OpenAI-412991?style=for-the-badge&logo=openai&logoColor=white
[OpenAI-url]: https://platform.openai.com/
[SQLite]: https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white
[SQLite-url]: https://www.sqlite.org/
[JavaScript]: https://img.shields.io/badge/JavaScript-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black
[JavaScript-url]: https://developer.mozilla.org/en-US/docs/Web/JavaScript
[Docker]: https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white
[Docker-url]: https://www.docker.com/
