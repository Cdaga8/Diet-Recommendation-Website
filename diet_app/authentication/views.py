from django.shortcuts import redirect, render
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.core.mail import send_mail
from django.contrib.sites.shortcuts import get_current_site
from diet_app import settings
from .models import UserProfile
from langchain_community.llms import Ollama
import ast

def home(request):
    return render(request, "authentication/index.html")

def signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']

        if User.objects.filter(username=username):
            messages.error(request, 'Username already exists!')
            return redirect('home')
        if User.objects.filter(email=email):
            messages.error(request, 'Email already exists!')
            return redirect('home')

        if len(username) > 10:
            messages.error(request, 'Username should not exceed 10 characters!')

        if pass1 != pass2:
            messages.error(request, 'Passwords do not match!')

        if not username.isalnum():
            messages.error(request, 'Username should contain only alphanumeric characters!')
            return redirect('home')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.save()

        messages.success(request, 'Your account has been successfully created!')

        # welcome email
        subject = "Welcome to Diet APP"
        message = f"Hello {myuser.first_name}! Welcome to Diet APP!"
        from_email = settings.EMAIL_HOST_USER
        to_list = [myuser.email]
        send_mail(subject, message, from_email, to_list, fail_silently=True)
        return redirect('signin')

    return render(request, "authentication/signup.html")

def signin(request):
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        user = authenticate(username=username, password=pass1)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid credentials!')
            return redirect('home')

    return render(request, "authentication/signin.html")

def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect('home')

def dashboard(request):
    if request.method == 'POST':
        age = request.POST['age']
        gender = request.POST['gender']
        weight = request.POST['weight']
        height = request.POST['height']
        dietary_preferences = request.POST['dietary_preferences']
        allergies = request.POST['allergies']
        health_goals = request.POST['health_goals']
        activity = request.POST.get('activity')

        UserProfile.objects.create(
            user=request.user,
            age=age,
            gender=gender,
            weight=weight,
            height=height,
            dietary_preferences=dietary_preferences,
            allergies=allergies,
            health_goals=health_goals,
            activity=activity
        )
        messages.success(request, 'Your information has been successfully saved!')
        return redirect('dailyDiet')

    return render(request, "authentication/dashboard.html")


def dailyDiet(request):
    username=request.user
    user = UserProfile.objects.get(user=username)
    age = user.age
    gender = user.gender
    height = user.height
    weight = user.weight
    dietary_preferences=user.dietary_preferences
    allergies=user.allergies
    health_goals=user.health_goals
    calories=bmr(height=height, weight=weight,age=age,gender=gender)
    protein=getProtein(weight=weight,goal=health_goals)
    fat=getFat(weight=weight,goal=health_goals)
    carbs=getCarb(protein=protein, fats=fat, cal=calories)
    veg=True if dietary_preferences=='True' else False
    Response_From_LLM=getDiet(calories=calories,protein=protein,carbs=carbs,fat=fat,elergy=allergies,veg=veg)
    print(Response_From_LLM)
    dictionary = ast.literal_eval(Response_From_LLM)
    breakfast=dictionary['Breakfast']
    lunch=dictionary['Lunch']
    snaks=dictionary['Snacks']
    dinner=dictionary['Dinner']
    return render(request,"authentication/dailyDiet.html",{'breakfast':breakfast,'lunch':lunch,'snacks':snaks,'dinner':dinner})

    

def getDiet(calories,protein,carbs,fat,elergy,veg):
    prompt=f'''daily calories needed: {calories}, protein needed:{protein}g, carbohydrates needed:{carbs}g, Fat needed:{fat}g'''
    if(veg==True):
        ss='I only want vegitarian options'
    else:
        ss='I want vegitarian or non-vegitarian options'
    query=f"""
    You are experienced dietitian and i want you to suggest me some diet plan for a day for my requirement.
    Provide just the answer to my questions no explanations are required.
    #The question will provide you to my daily calories need protein needed, and carbohydrates required, and fat needed.
    #Question:{prompt}
    -> Keep in mind That i have elergy from {elergy}
    -> {ss}
    #Provide the Response in python Dictonory format as follow Breakfast, lunch, snaks and dinner.
    #the dictionary will have following format it will have Lunch, Breakfast, Dinner and Snacks columns.
    #give Response in 100 words.
    #Only provide answer string
    
    """

    llm = Ollama(model="llama3")

    response= llm.invoke(query)

    return response

def bmr(height, weight, gender,age):
    if gender=='male':
        bmr=(10*weight)+(6.25*height)-(5*age)+5
    else:
        bmr=(10*weight)+(6.25*height)-(5*age)-161
    return bmr


def cal(tdee,goal):
    if goal=='WeightGain':
        cal=tdee+500
    elif goal=='Maintain-Weight':
        cal=tdee
    else:
        cal=tdee-500
    return cal

def getProtein(weight, goal):
    if goal=='WeightGain':
        protein=weight*1.2
    elif goal=='Maintain-Weight':
        protein=weight*0.8
    else:
        protein=weight*1.6
    return protein

def getFat(weight, goal):
    if goal=='WeightGain':
        fats=weight*1
    elif goal=='Maintain-Weight':
        fats=weight*0.8
    else:
        fats=weight*0.5
    return fats

def getCarb(protein, fats, cal):
    carbs = cal-protein-fats
    return carbs