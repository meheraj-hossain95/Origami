# 🎯 Origami - Personal Productivity & Wellness App

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![PySide6](https://img.shields.io/badge/PySide6-6.9.2-green.svg)](https://pypi.org/project/PySide6/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Origami** is a comprehensive desktop productivity and wellness application built with Python and PySide6. It combines essential productivity tools in a clean, modern interface inspired by popular platforms like Google and Facebook.

![Origami App Screenshot](assets/screenshots/dashboard.png)

## ✨ Features

### 🏠 **Dashboard**
- **Time-based greetings** - Personalized welcome messages based on time of day
- **Motivational quotes** - Daily inspiration to keep you motivated
- **Task completion overview** - Visual progress tracking of your daily tasks
- **Upcoming events** - Quick view of your calendar events
- **Clean, modern interface** - Professionally designed UI with dark/light theme support

### ✅ **Task Management**
- **Simple todo creation** - Quick task entry with intuitive interface
- **Task completion tracking** - Visual progress indicators and statistics
- **Modern list interface** - Clean, organized task display
- **Real-time updates** - Instant sync between dashboard and task views

### 📝 **Digital Journal**
- **Secure journaling** - Optional password protection for privacy
- **Rich text editing** - Advanced text formatting capabilities
- **Date-based entries** - Organized by date for easy navigation
- **Search functionality** - Find entries quickly with built-in search
- **Encrypted storage** - Your thoughts remain private and secure

### 📅 **Smart Calendar**
- **Event management** - Create, edit, and delete calendar events
- **Modern calendar view** - Clean, intuitive month/week navigation
- **Dashboard integration** - Upcoming events shown on main dashboard
- **Time-aware scheduling** - Smart event organization

### ⏰ **Focus Timer (Pomodoro)**
- **Customizable sessions** - Adjustable work and break durations
- **Session tracking** - Monitor your focus sessions and productivity
- **Desktop notifications** - Stay informed without watching the clock
- **Professional timer interface** - Distraction-free focus environment

### 👤 **User Profile Management**
- **Personal customization** - Set your name and display preferences
- **Theme switching** - Choose between light and dark modes
- **Security settings** - Manage password protection for sensitive features
- **Personalized experience** - Tailored greetings and interface

### 🎨 **Modern Design**
- **Responsive interface** - Clean, professional design
- **Dark/Light themes** - Choose your preferred visual style
- **Intuitive navigation** - Easy-to-use sidebar navigation
- **Professional styling** - Inspired by modern web applications

## 🚀 Installation

### Prerequisites
- **Python 3.8 or higher**
- **Windows, macOS, or Linux**

### Option 1: Quick Setup (Recommended)

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/origami.git
   cd origami
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python main.py
   ```

### Option 2: Virtual Environment (Recommended for Development)

1. **Clone and navigate**
   ```bash
   git clone https://github.com/yourusername/origami.git
   cd origami
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Launch Origami**
   ```bash
   python main.py
   ```

## 💻 How to Use

### Getting Started

1. **Launch the application** by running `python main.py`
2. **Set up your profile** by clicking the "User" button in the sidebar
3. **Customize your experience** by choosing your preferred theme (light/dark)
4. **Start being productive!** 

### Core Workflows

#### 📋 Managing Tasks
1. Navigate to **Tasks** in the sidebar
2. Click the input field and type your task
3. Press Enter or click Add to create the task
4. Check off completed tasks
5. View your progress on the Dashboard

#### 📖 Digital Journaling
1. Go to **Journal** section
2. Set up password protection (optional but recommended)
3. Select a date or use today's date
4. Write your thoughts in the rich text editor
5. Your entries are automatically saved and encrypted

#### 📅 Calendar Management
1. Open the **Calendar** section
2. Click on any date to add an event
3. Fill in event details (title, time, description)
4. View upcoming events on your Dashboard

#### ⏱️ Focus Sessions
1. Access **Focus Timer** from the sidebar
2. Customize your work/break durations if needed
3. Click Start to begin a focus session
4. Take breaks when prompted
5. Track your productivity over time

### Keyboard Shortcuts
- **Ctrl+1-5**: Quick navigation between main sections
- **Escape**: Close dialogs and return to main view

## 🔧 Configuration

The app stores its configuration and data in:
- **Windows**: `%APPDATA%/Origami/`
- **macOS**: `~/Library/Application Support/Origami/`
- **Linux**: `~/.config/Origami/`

### Customization Options

- **Themes**: Switch between light and dark modes
- **Pomodoro Settings**: Adjust work/break durations
- **Security**: Enable/disable password protection for journal
- **Notifications**: Control desktop notification preferences

## 🛠️ Development

### Project Structure

```
origami/
├── main.py                 # Application entry point
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── assets/                # Icons and images
│   └── icons/
├── data/                  # Database and user data
├── database/              # Database models and connection
│   ├── __init__.py
│   ├── db.py
│   └── models.py
├── logic/                 # Business logic
│   ├── __init__.py
│   ├── pomodoro_logic.py
│   └── todo_logic.py
├── ui/                    # User interface components
│   ├── __init__.py
│   ├── main_window.py
│   ├── todo_ui.py
│   ├── journal_ui.py
│   ├── calendar_ui.py
│   ├── pomodoro_ui.py
│   └── profile_ui.py
└── utils/                 # Utility functions
    ├── __init__.py
    ├── encryption.py
    ├── helpers.py
    └── notifications.py
```

### Dependencies

- **PySide6** (6.9.2) - Cross-platform GUI framework
- **SQLAlchemy** (2.0.43) - Database ORM
- **cryptography** (45.0.7) - Encryption for journal entries
- **requests** (2.32.4) - HTTP requests for future features
- **plyer** (2.1.0) - Cross-platform notifications

### Running Tests

```bash
# Install development dependencies
pip install pytest pytest-qt

# Run tests
pytest
```

## 🤝 Contributing

We welcome contributions to make Origami even better! Here's how you can help:

### Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally
   ```bash
   git clone https://github.com/yourusername/origami.git
   ```
3. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Set up development environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Development Guidelines

#### Code Style
- Follow **PEP 8** Python style guidelines
- Use **descriptive variable names**
- Add **docstrings** for functions and classes
- Keep functions **focused and small**

#### UI Guidelines
- Maintain **consistent theming** (check both light and dark modes)
- Ensure **responsive design** across different window sizes
- Follow **accessibility best practices**
- Test UI changes on **multiple platforms** if possible

#### Commit Guidelines
- Use **clear, descriptive commit messages**
- Reference **issue numbers** when applicable
- Keep commits **focused and atomic**

### Types of Contributions

#### 🐛 Bug Reports
- Use the **issue template**
- Include **steps to reproduce**
- Specify your **operating system and Python version**
- Add **screenshots** if relevant

#### ✨ Feature Requests
- **Describe the problem** your feature would solve
- **Explain your proposed solution**
- Consider **alternative approaches**
- Check if similar features **already exist**

#### 🔧 Code Contributions
- **Implement bug fixes** or new features
- **Add tests** for your changes
- **Update documentation** as needed
- **Ensure backwards compatibility**

#### 📖 Documentation
- **Improve README** or other docs
- **Add code comments** for clarity
- **Create tutorials** or guides
- **Fix typos** and grammar

### Development Workflow

1. **Check existing issues** before starting work
2. **Discuss major changes** in an issue first
3. **Write tests** for new functionality
4. **Test thoroughly** on your platform
5. **Submit a pull request** with clear description

### Pull Request Process

1. **Update documentation** if needed
2. **Add tests** for new features
3. **Ensure all tests pass**
4. **Request review** from maintainers
5. **Address feedback** promptly

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

```
MIT License

Copyright (c) 2025 Origami

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🙏 Acknowledgments

- **PySide6 team** for the excellent GUI framework
- **Python community** for amazing libraries
- **Contributors** who help make Origami better
- **Users** who provide feedback and suggestions

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/origami/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/origami/discussions)
- **Email**: origami.productivity@gmail.com

---

**Made with ❤️ for productivity enthusiasts**

*Origami - Fold your chaos into clarity*