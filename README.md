# Bloom 🌸

Bloom is a Django-based flower boutique web application designed to provide a simple and elegant online experience for discovering and purchasing flowers.

## ✨ Features

* User registration and login
* Secure Django authentication
* Bloom Atelier themed login and signup pages
* Flower/product browsing
* Product details
* Shopping cart functionality
* Order management
* User account management
* Responsive and elegant interface
* Django admin panel for managing application data

## 🛠️ Technologies Used

* **Python**
* **Django 5.2**
* **HTML5**
* **CSS3**
* **Tailwind CSS**
* **JavaScript**
* **SQLite** for development
* **Git & GitHub** for version control

## 📁 Project Structure

```text
bloom/
├── accounts/
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   └── ...
├── templates/
│   └── accounts/
│       ├── login.html
│       └── signup.html
├── bloom/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── manage.py
└── requirements.txt
```

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/nireezalsweidan/Bloom
cd Bloom-FinalProject
```

Create and activate a virtual environment:

```bash
python -m venv venv
```

On Windows:

```bash
venv\Scripts\activate
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

Run the database migrations:

```bash
python manage.py migrate
```

Start the development server:

```bash
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## 👤 Authentication

Bloom uses Django's authentication system for user registration and login.

Users can:

* Create an account
* Log in using their credentials
* Log out securely
* Access authenticated features of the application

The authentication pages use the custom Bloom Atelier interface while keeping Django's backend authentication functionality.

## 🎨 Design

The interface follows the Bloom Atelier visual identity, using:

* Soft neutral backgrounds
* Botanical/flower imagery
* Dark green typography
* Elegant serif headings
* Clean, minimal layouts
* Responsive components

The goal is to create a calm and welcoming experience inspired by a modern floral boutique.

## 📌 Development

This project was developed as a Django web application, combining Django's backend functionality with a custom frontend design.

The project is intended for educational and development purposes.

## 👩‍💻 Authors

**Nireez Al Sweidan**

Bloom — Final Project
