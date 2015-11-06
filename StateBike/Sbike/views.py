from django.shortcuts import render
from django.contrib.auth.models import User
from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist

from .forms import ClientRegisterForm
from .models import Client
from .models import Admin
from .models import Employee
from .models import Station
from .models import Bike
from .models import Loan

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def principal(request):
    return render(request, 'Sbike/index.html')

def clientRegisterView(request):
    if request.user.is_authenticated():
        return redirect('/webprofile')

    if request.method == 'POST':
        form = ClientRegisterForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            username = cleaned_data.get('username')
            password = cleaned_data.get('password1')
            first_name = cleaned_data.get('first_name')
            last_name = cleaned_data.get('last_name')
            email = cleaned_data.get('email')
            phone_number = cleaned_data.get('phone_number')
            dni = cleaned_data.get('dni')
            card_number = cleaned_data.get('card_number')
            expiration_date = cleaned_data.get('expiration_date')
            security_code = cleaned_data.get('security_code')

            user = User.objects.create_user(username, email, password)

            user.first_name = first_name
            user.last_name = last_name

            user.save()

            client = Client()
            client.user = user
            client.phone_number = phone_number
            client.dni = dni
            client.card_number = card_number
            client.expiration_date = expiration_date
            client.security_code = security_code

            client.save()
            return redirect('/weblogin')

    else:
        form = ClientRegisterForm()
    context = {
        'form' : form
    }
    return render(request, 'Sbike/client_register.html', context)

def locatorView(request):
    stations = Station.objects.all()
    return render(request, 'Sbike/stations.html', {'stations':stations})

def home(request):
    return render(request,'Sbike/home.html')

@login_required
def bikeLoan(request):
    if request.method == 'POST':
        bike_id = request.POST.get('select')
        
        Bike.objects.filter(id=bike_id).update(state='TK')
        loan = Loan()
        loan.client = request.POST.get('username')
        loan.bike = bike_id
        loan.save()

        messages.success(request, 'Tomaste la bicicleta id : '+str(bike_id))
        return redirect('/webprofile')
    ####PENSAR EN COMO ELIMINAR LA POSIBILIDAD DE VOLVER A PEDIR
    bikes = Bike.objects.filter(state='AV')
    if len(bikes) == 0:
        messages.error(request, 'Sorry, No Bikes Available!')
    return render(request, 'Sbike/bike_loan.html', ({'bikes' : bikes}))


def webLoginView(request):
    if request.user.is_authenticated():
        return redirect('/webprofile')

    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/webprofile')
            else:
                message = 'Inactive User'
                return render(request, 'login.html', {'message' : message})
        message = 'Invalid username/password'
    return render(request, 'Sbike/web_login.html', {'message' : message})

def stationLoginView(request):
    if request.user.is_authenticated():
        return redirect('/stationprofile')
    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/stationprofile')
            else:
                message = 'Inactive User'
                return render(request, 'login.html', {'message' : message})
        message = 'Invalid username/password'
    return render(request, 'Sbike/station_login.html', {'message' : message})

def morir():
    return HttpResponse('estas muerto')

#EVITAR REPETIR CODIGO

@login_required
def stationProfile(request):
    username = request.user.get_username()
    clients = Client.objects.filter(user__username=username)

    if len(clients) == 1:
        # create basic info dict
        dict = createUserDict(clients[0])

        # add extra client info
        #QUITAR TANTOS [0] Y REEMPLEZARLOS POR UNA VARIABLE
        dict['card_number'] = clients[0].card_number
        dict['exp_date'] = clients[0].expiration_date
        dict['sec_code'] = clients[0].security_code

        return render(request, 'Sbike/station_profile.html', dict)
        
    else:
        logout(request)
        messages.error(request, 'Admin/Employee can not login!')
        return redirect('/stationlogin')

@login_required
def webProfile(request):

        username = request.user.get_username()
        clients = Client.objects.filter(user__username=username)
        admins = Admin.objects.filter(user__username=username)
        employees = Employee.objects.filter(user__username=username)

        if len(clients) == 1:
            return clientProfile(request, clients[0])


        elif len(admins) == 1 or username == 'admin':
            if len(admins) == 0:
                message = 'Usted es el admin de django. PENSAR BIEN ESTA SITUACION'
                return render(request, 'Sbike/admin_profile.html', {'message' : message})
            else:
                return adminProfile(request, admins[0])


        elif len(employees) == 1:
            return employeeProfile(request, employees[0])

#Esto que sigue ya no deberia volver a ocurrir.
#Si alguien lo detecta. Avise!!
        else:
            return HttpResponse('Error: Hay un usuario logueado inexistente en la base de datos o varios usuarios comparten el mismo username "%s"' % username)

def clientProfile(request, client):

    # create basic info dict
    dict = createUserDict(client)

    # add extra client info
    dict['card_number'] = client.card_number
    dict['exp_date'] = client.expiration_date
    dict['sec_code'] = client.security_code

    return render(request, 'Sbike/client_profile.html', dict)

def adminProfile(request, admin):

    dict = createUserDict(admin)
    return render(request, 'Sbike/admin_profile.html', dict)

def employeeProfile(request, employee):

    dict = createUserDict(employee)
    return render(request, 'Sbike/employee_profile.html', dict)

def createUserDict(sbuser):

    dict = {}
    dict['fname'] = sbuser.user.first_name
    dict['lname'] = sbuser.user.last_name
    dict['username'] = sbuser.user.username
    dict['email'] = sbuser.user.email
    dict['dni'] = sbuser.dni
    dict['phone'] = sbuser.phone_number

    return dict


@login_required
def locatorView(request):
    stations = Station.objects.all()
    return render(request, 'Sbike/stations.html', {'stations':stations})

def webLoginView(request):
    if request.user.is_authenticated():
        return redirect('/webprofile')

    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/webprofile')
            else:
                message = 'Inactive User'
                return render(request, 'login.html', {'message' : message})
        message = 'Invalid username/password'
    return render(request, 'Sbike/web_login.html', {'message' : message})

def stationLoginView(request):
    if request.user.is_authenticated():
        return redirect('/stationprofile')

    message = ''
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/stationprofile')
            else:
                message = 'Inactive User'
                return render(request, 'login.html', {'message' : message})
        message = 'Invalid username/password'
    return render(request, 'Sbike/station_login.html', {'message' : message})

@login_required
def logoutView(request):
    logout(request)
    messages.success(request, 'You have successfully logged out!')
    return redirect('/weblogin')
