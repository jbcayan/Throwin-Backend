# Throwin Backend API

## Table of Contents

- [Table of Contents](#table-of-contents)   
- [Introduction](#introduction)
- [Installation](#installation)
- [Installation By Docker](#installation-by-docker)


## Introduction

This is a sample backend API for throwin. Based on a consumer can give a tip or review of  the restaurant stuff.


## Installation
_`Get the .env file and install the dependencies`_

```bash
git clone https://github.com/jbcayan/Throwin-Backend.git
```

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

```bash
cd throwin
```

```bash
python manage.py runserver
```


## Installation By Docker
_`Get the .env file and install the dependencies`_

```bash
git clone https://github.com/jbcayan/Throwin-Backend.git
```

```bash
cd Throwin-Backend
```

```bash
docker compose up --build
```

```bash
docker compose down
```
