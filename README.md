# Item Catalog Application 

>Users can create, edit and delete categories. They can create items inside the categories, edit or delete them.

>The website utilizes Google OAuth2 API for users login. Users can edit and delete only their own categories or items.


## Project Overview
You will develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.

## Why This Project?
Modern web applications perform a variety of functions and provide amazing features and utilities to their users; but deep down, it’s really all just creating, reading, updating and deleting data. In this project, you’ll combine your knowledge of building dynamic websites with persistent data storage to create a web application that provides a compelling service to your users.

## What Will I Learn?
You will learn how to develop a RESTful web application using the Python framework Flask along with implementing third-party OAuth authentication. You will then learn when to properly use the various HTTP methods available to you and how these methods relate to CRUD (create, read, update and delete) operations.

# Requirement
  * [Python3](https://www.python.org/)
  * [Udacity Vagrant](https://github.com/udacity/fullstack-nanodegree-vm)
  * [VirtualBox](https://www.virtualbox.org/)

# How to install 
	1- install Vagrant & VirtualBox
	2- Clone The Udacity Vagrantfile
	3- Go to vagrant directry and clone this repo
	4- Launch the VM using ('vagrant up')
	5- log in using ('vagant ssh')
	6- Access the application folder via ('cd /vagrant')
	7- Run the application by using the command (pyton application.py)
	8- Access the application [locally](http://localhost:5000)


#JSON Endpoints
you can access the json data of the project through :

	1- to show all catagories JSON file "/category/JSON"
	2- to show view all items in a category "/category/<int:category_id>/item/JSON"
	3- to show a particular item "/category/<int:category_id>/item/<int:item_id>/JSON"