from django.shortcuts import render
from django.shortcuts import redirect

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db import IntegrityError

from .forms import ClientRegisterForm, ClientEditPhoneForm, ClientEditEmailForm
from .forms import ClientEditNameForm, ClientEditPasswordForm
from .forms import ClientEditCardDataForm, CreateStationForm, RegisterForm

from itertools import chain

from .models import Client
from .models import Admin
from .models import Employee
from .models import Station
from .models import Bike
from .models import Loan
from .models import Sanction
from .models import Notification

from random import randint  # para las estaciones


# ##-----------------------------------------------------------------------## #
# ##----------------------------REGISTER-----------------------------------## #
# ##-----------------------------------------------------------------------## #
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

            client.edit_card(card_number, expiration_date, security_code)

            messages.success(request, 'You Have Successfully Registered')
            return redirect('/weblogin')

    else:
        form = ClientRegisterForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_register.html', context)
# ##-----------------------------------------------------------------------## #
# ##----------------------------END--REGISTER------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------------LOCATOR---------------------------------## #
# ##-----------------------------------------------------------------------## #
@login_required
def locatorView(request):
    stations = Station.objects.all()
    return render(request, 'Sbike/stations.html', {'stations': stations})

# ##-----------------------------------------------------------------------## #
# ##----------------------------END--LOCATOR-------------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##--------------------------------HOME-----------------------------------## #
# ##-----------------------------------------------------------------------## #


def home(request):
    logout(request)
    return render(request, 'Sbike/home.html')

# ##-----------------------------------------------------------------------## #
# ##-----------------------------END--HOME---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------WEB--LOGIN---------------------------------## #
# ##-----------------------------------------------------------------------## #

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
                request.session['type'] = 'web'
                if Admin.objects.filter(user=user).first() is not None:
                    request.session['user_type'] = 'admin'
                elif Employee.objects.filter(user=user).first() is not None:
                    request.session['user_type'] = 'employee'
                else:
                    request.session['user_type'] = 'client'
                return redirect('/webprofile')
            else:
                message = 'Inactive User'
                return render(request, 'login.html', {'message': message})
        message = 'Invalid username/password'
    return render(request, 'Sbike/web_login.html', {'message': message})

# ##-----------------------------------------------------------------------## #
# ##----------------------------WEB--LOGIN---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------STATION--LOGIN-------------------------------## #
# ##-----------------------------------------------------------------------## #

def get_random_station():
    # asignar una estacion random
    stations = Station.objects.all()
    chosen = randint(0, len(stations) - 1)

    # seleccionar la estacion i-esima
    i = 0
    for st in stations:
        if i == chosen:
            break
        i = i + 1
    return st.id


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
                try:
                    request.session['station'] = get_random_station()
                except ValueError:
                    return render(
                        request, 'Sbike/station_login.html',
                        {'message': 'There is no existing station'})

                login(request, user)
                request.session['type'] = 'station'
                return redirect('/stationprofile')
            else:
                return render(
                    request, 'Sbike/station_login.html',
                    {'message': 'Inactive User'})
        message = 'Invalid username/password'
    return render(request, 'Sbike/station_login.html', {'message': message})


# ##-----------------------------------------------------------------------## #
# ##------------------------END--STATION--LOGIN----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------------LOGOUT-----------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def logoutView(request):

    messages.success(request, 'You have successfully logged out!')
    s_type = request.session['type']
    logout(request)
    if (s_type == 'station'):
        return redirect('/stationlogin')
    return redirect('/weblogin')
# ##-----------------------------------------------------------------------## #
# ##-----------------------------END--LOGOUT-------------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##---------------------------STATION-PROFILE-----------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def stationProfile(request):
    username = request.user.get_username()
    clients = Client.objects.filter(user__username=username)

    if len(clients) == 1:
        # create basic info dict
        dict = createUserDict(clients[0])

        # add extra client info
        dict['card_number'] = clients[0].card_number
        dict['exp_date'] = clients[0].expiration_date
        dict['sec_code'] = clients[0].security_code

        return render(request, 'Sbike/station_profile.html', dict)

    else:
        logout(request)
        messages.error(request, 'Admin/Employee can not login!')
        return redirect('/stationlogin')

# ##-----------------------------------------------------------------------## #
# ##-----------------------END--STATION-PROFILE----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##---------------------------WEB-PROFILE---------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def webProfile(request):

        username = request.user.get_username()
        clients = Client.objects.filter(user__username=username)
        admins = Admin.objects.filter(user__username=username)
        employees = Employee.objects.filter(user__username=username)

        if len(clients) == 1:
            return clientProfile(request, clients[0])

        elif len(admins) == 1:
                return adminProfile(request, admins[0])

        elif len(employees) == 1:
            return employeeProfile(request, employees[0])

# Esto que sigue ya no deberia volver a ocurrir.
# Si alguien lo detecta. Avise!!
        else:
            messages.error(request, 'Error: Access Denied')
            return redirect('/home')
# ##-----------------------------------------------------------------------## #
# ##------------------------END--WEB--PROFILE------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------PROFILE--FUNCTS-------------------------------## #
# ##-----------------------------------------------------------------------## #


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

    # add notifications into dict
    dict['notif'] = Notification.objects.all()
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

# ##-----------------------------------------------------------------------## #
# ##-------------------------PROFILE--FUNCTS-------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-----------------------------LOANS-------------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def bikeLoan(request):
    if request.method == 'POST':

        client = Client.objects.get(user=request.user)
        try:
            bike_id = request.POST.get('select')
            bike = Bike.objects.get(id=bike_id)
            station = Station.objects.get(id=bike.station.id)
            loan = Loan()
            loan.create_loan(client, bike)

            # update data base after possible exception
            Bike.objects.filter(id=bike_id).update(state='TK')
            if station.remove_from_stock():
                notif = Notification()
                notif.add_station(station)

            messages.success(request, 'Loan: Bike '+str(bike_id))
        except IntegrityError:
            messages.error(request, 'Sorry, You Have An Outstanding Loan')
        finally:
            return redirect('/stationprofile')
    bikes = Bike.objects.filter(state='AV',
                                station_id=request.session['station'])
    if len(bikes) == 0:
        messages.error(request, 'Sorry, No Bikes Available!')
    return render(request, 'Sbike/bike_loan.html', ({'bikes': bikes}))

# ##-----------------------------------------------------------------------## #
# ##----------------------------END--LOANS---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------GIVE--BACK---------------------------------## #
# ##-----------------------------------------------------------------------## #
class SanctionExist(Exception):
    pass


@login_required
def givebackView(request):
    station = Station.objects.get(id=request.session['station'])
    if request.method == 'POST':
        bike_id = request.POST.get('select')

        station.add_to_stock()

        loan = Loan.objects.get(bike=bike_id)
        loan.set_end_date()
        days = loan.eval_sanction()

        if days > 0:
            sanction = Sanction()
            sanction.create_sanction(loan, days)
        else:
            Loan.objects.filter(bike=bike_id).delete()

        # actualizar info de la bicicleta
        bike = Bike.objects.get(id=bike_id)
        bike.give_back()
        bike.move(station)

        message = 'Thanks For Return!'
        return render(request, 'Sbike/give_back.html', {'message': message})

    # check if there is capacity available
    if station.stock >= station.capacity:
        messages.error(
            request,
            'Sorry! There is no capacity in the station ' + station.name)
        return render(request, 'Sbike/give_back.html')
    client = Client.objects.get(user=request.user)
    try:
        # check if a sanction exists
        if (Sanction.objects.filter(client=client).first()) is not None:
            raise SanctionExist

        loan = Loan.objects.get(client=client)
        bike = Bike.objects.get(id=loan.bike.id)
        return render(request, 'Sbike/give_back.html', {'bike': bike})
    except SanctionExist:
        messages.error(request, 'Sorry! A Sanction is Pending')
        return render(request, 'Sbike/give_back.html')
    except ObjectDoesNotExist:
        messages.error(request, 'Sorry! No Loans Outstanding!!')
        return render(request, 'Sbike/give_back.html')

# ##-----------------------------------------------------------------------## #
# ##------------------------END--GIVE--BACK--------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------EDIT---PASSWORD--------------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def clientEditPassword(request):
    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        form = ClientEditPasswordForm(request.POST)

        if form.is_valid():
            cleaned_data = form.cleaned_data
            """comprueba cada campo que no este vacio"""
            """si no lo esta entonces modifica la base"""

            password = make_password(cleaned_data['password1'])
            if password:
                client.user.password = password
                messages.success(request, 'Password Changed Successfully')
            else:
                messages.error(request, 'Error! Password Null!')
            client.user.save()
            return redirect('/webprofile')

    form = ClientEditPasswordForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------------END--EDIT--PASSWORD------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------EDIT--CLIENT--CARD--DATA----- ---------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def clientEditCardData(request):

    client = Client.objects.get(user=request.user)
    if request.method == 'POST':
        form = ClientEditCardDataForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            """comprueba cada campo que no este vacio"""
            """si no lo esta entonces modifica la base"""
            card_number = cleaned_data['card_number']
            expiration_date = cleaned_data['expiration_date']
            security_code = cleaned_data['security_code']

            client.edit_card(card_number, expiration_date, security_code)

            messages.success(request, 'Successfully Update!')
            return redirect('/editprofile/card')
    form = ClientEditCardDataForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)

# ##-----------------------------------------------------------------------## #
# ##-------------------END--EDIT--CLIENT--CARD--DATA-----------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------EDIT--CLIENT--PHONE------------------------------## #
# ##-----------------------------------------------------------------------## #
@login_required
def ClientEditPhone(request):
    client = Client.objects.get(user=request.user)

    if request.method == 'POST':
        form = ClientEditPhoneForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data
            phone_number = cleaned_data['phone_number']
            client.edit_phone(phone_number)
            messages.success(
                request, 'Successfully Update! Phone: ' + str(phone_number))
            return redirect('/editprofile/phone')

    form = ClientEditPhoneForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------END--EDIT--CLIENT--PHONE-------------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##------------------------EDIT--CLIENT--EMAIL----------------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def ClientEditEmail(request):
    client = Client.objects.get(user=request.user)

    if request.method == 'POST':
        form = ClientEditEmailForm(request.POST)
        if form.is_valid():
            email = form.clean_email()
            client.edit_email(email)
            messages.success(
                request, 'Successfully Update! Email: ' + str(email))
            return redirect('/editprofile/email')

    form = ClientEditEmailForm()
    context = {
        'form': form
    }
    return render(request, 'Sbike/client_edit.html', context)


# ##-----------------------------------------------------------------------## #
# ##----------------------END--EDIT--CLIENT--EMAIL-------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##--------------------------SET-BIKE-STATUS------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def setBikeStatus(request):
    try:
        # ver si es realmente un empleado
        SMaster = Employee.objects.get(user=request.user)
        # obtener todas las estaciones a cargo del empleado
        Stations = Station.objects.filter(employee=SMaster)

        # action es la accion a realizar
        # y bike_id es la bicileta a la cual aplicar
        if request.method == 'POST':
            bike_id = request.POST.get('bike_id')
            action = request.POST.get('Action')
            try:
                bike = Bike.objects.get(id=bike_id)
                if action == 'Repair':
                    bike.state = 'AV'
                    messages.success(request, 'bike repaired!')
                elif action == 'Set as broken':
                    bike.state = 'BR'
                    messages.success(request, 'bike not longer available!')
                bike.save()
            except Bike.DoesNotExist:
                messages.error(request, 'that bike not exist!')

        # obtener solo las bicis rotas que estan
        # en estaciones a cargo del empleado
        try:
            context = dict()
            context['brokenbikes'] = []
            context['availablebikes'] = []
            for S in Stations:
                filterargsA = {'state': 'AV', 'station': S}
                available = Bike.objects.filter(**filterargsA)
                context['availablebikes'].extend(list(available))
                filterargsB = {'state': 'BR', 'station': S}
                broken = Bike.objects.filter(**filterargsB)
                context['brokenbikes'].extend(list(broken))
        except Bike.DoesNotExist:
            messages.error(request, 'not are bikes here')

        return render(request, 'Sbike/set_bike_status.html', context)
    except Employee.DoesNotExist:
        messages.error(
            request, 'You not have permissions to perform this action')
        return redirect('/stationprofile')

# ##-----------------------------------------------------------------------## #
# ##------------------------END-SET-BIKE-STATUS----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##-------------------------CREATE--STATION-------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def createStation(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            employee_dni = request.POST.get('select')
            employee = Employee.objects.get(dni=employee_dni)
            form = CreateStationForm(request.POST)
            if form.is_valid():
                cleaned_data = form.cleaned_data
                name = cleaned_data['name']
                address = cleaned_data['address']
                stock = cleaned_data['stock']
                capacity = cleaned_data['capacity']

                station = Station()
                station.create_station(
                    employee, name, address, stock, capacity)
                messages.success(request, 'Station Successfully Created!')

                return redirect('/webprofile')

        employees = Employee.objects.all()

        if not employees.exists():
            messages.error(request, 'No registered Employee!')
            return redirect('/webprofile')

        form = CreateStationForm()
        context = {
            'form': form,
            'employees': employees
        }

        return render(request, 'Sbike/create_station.html', context)

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')

# ##-----------------------------------------------------------------------## #
# ##-------------------------END--CREATE--STATION--------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##---------------------ASSIGN--EMPLOYEE-TO-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def assignEmployee(request):
    if request.method == 'POST':
        try:
            employee_dni = request.POST.get('selectemployee')
        except IntegrityError:
            messages.error(request, 'Error! 123!')
        finally:
            request.session['employee_to_assign'] = int(employee_dni)
            return redirect('/assignstation')

    employees = Employee.objects.all()
    if len(employees) == 0:
        messages.error(request, 'Sorry, No Employees!')
    return render(
        request, 'Sbike/assign_employee.html', {'employees': employees})


@login_required
def assignStation(request):
    if request.method == 'POST':
        try:
            station_id = request.POST.get('selectstation')
            employee = Employee.objects.filter(
                dni=int(request.session['employee_to_assign']))
            station = Station.objects.filter(id=station_id)
            station.update(employee=employee[0])
            employee.update(is_assigned=True)
        except IntegrityError:
            messages.error(request, 'Error! 123!')
        finally:
            msg0 = 'Employee Assigned: ' + str(employee[0].user)
            msg = msg0 + ' - Station: ' + str(station[0].name)
            messages.success(request, msg)
            return redirect('/webprofile')

    stations = Station.objects.filter(employee__isnull=True)
    if len(stations) == 0:
        messages.error(request, 'Sorry, No Free Stations!')
    return render(request, 'Sbike/assign_station.html', {'stations': stations})


# ##-----------------------------------------------------------------------## #
# ##----------------END--ASSIGN--EMPLOYEE-TO-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##-----------------UNASSIGN--EMPLOYEE-FROM-STATION-----------------------## #
# ##-----------------------------------------------------------------------## #


@login_required
def unassignEmployee(request):
    if request.method == 'POST':
        try:
            employee_dni = request.POST.get('selectemployee')
        except IntegrityError:
            messages.error(request, 'Error! 123!')
        finally:
            request.session['employee_to_unassign'] = int(employee_dni)
            return redirect('/unassignstation')

    employees = Employee.objects.filter(is_assigned=True)
    if len(employees) == 0:
        messages.error(request, 'Sorry, No Employees Assigned!')
    return render(
        request, 'Sbike/unassign_employee.html', ({'employees': employees}))


@login_required
def unassignStation(request):
    if request.method == 'POST':
        try:
            station_id = request.POST.get('selectstation')
            employee = Employee.objects.filter(
                dni=int(request.session['employee_to_unassign']))
            station = Station.objects.filter(id=station_id)
            station.update(employee=None)
            if (request.session['stations_assigned'] == 1):
                employee.update(is_assigned=False)
        except IntegrityError:
            messages.error(request, 'Error! 123!')
        finally:
            msg0 = 'Employee Unassigned: ' + str(employee[0].user)
            msg = msg0 + ' - Station: ' + str(station[0].name)
            messages.success(request, msg)
            return redirect('/webprofile')

    employee = Employee.objects.filter(
        dni=int(request.session['employee_to_unassign']))
    stations = Station.objects.filter(employee=employee)
    request.session['stations_assigned'] = len(stations)
    if len(stations) == 0:
        # No deberia ocurrir nunca
        messages.error(request, 'Sorry, No Assigned Stations!')
    return render(
        request, 'Sbike/unassign_station.html', {'stations': stations})


# ##-----------------------------------------------------------------------## #
# ##-----------------END--UNASSIGN--EMPLOYEE-FROM-STATION------------------## #
# ##-----------------------------------------------------------------------## #

# ##-----------------------------------------------------------------------## #
# ##---------------------------VIEW_CLIENTS--------------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def view_clients(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
            clients = Client.objects.all()
            clients2 = []
            for cli in clients:
                cliente = createUserDict(cli)
                sanction = Sanction.objects.filter(client=cli).first()
                cliente['sanction'] = sanction is not None
                clients2.append(cliente)

            return render(
                request, 'Sbike/view_clients.html', {'clients': clients2})

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')

# ##-----------------------------------------------------------------------## #
# ##--------------------------END--VIEW_CLIENTS----------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##----------------------------ADD-BIKE-----------------------------------## #
# ##-----------------------------------------------------------------------## #
def addBike(request):
    user_type = request.session['user_type']

    if user_type == 'admin':
        if request.method == 'POST':
            stationD = request.POST.get('select')
            bikeamount = request.POST.get('input')
            print "\nstationO: " + stationD
            print "   amoubt" + str(int(bikeamount))
            stationDes = Station.objects.filter(id=stationD)[0]
            stockAll = len(Bike.objects.filter(station=stationDes))
            if (stockAll + int(bikeamount)) <= stationDes.capacity:
                for i in range(0, int(bikeamount)):
                    bike = Bike()
                    bike.station = stationDes
                    bike.save()
                messages.success(
                    request, str(i+1) + ' bikes created in ' + stationDes.name)
                return redirect('/webprofile')
            else:
                msg0 = ' just have ' + str(stationDes.capacity - stockAll)
                msg = msg0 + ' spaces empty'
                messages.error(request, 'the station ' + stationDes.name + msg)

        station = Station.objects.all()

        if len(station) == 0:
            messages.error(request, 'There is no Created Stations!!')
            return redirect('/webprofile')

        return render(request, 'Sbike/add_bike.html', {'stations': station})
    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/stationprofile')

# ##-----------------------------------------------------------------------## #
# ##--------------------------END-ADD-BIKE---------------------------------## #
# ##-----------------------------------------------------------------------## #


# ##-----------------------------------------------------------------------## #
# ##------------------------REGISTER--EMPLOYEE-----------------------------## #
# ##-----------------------------------------------------------------------## #

@login_required
def employeeRegister(request):
    user_type = request.session['user_type']
    if user_type == 'admin':
        if request.method == 'POST':
            form = RegisterForm(request.POST)

            if form.is_valid():
                cleaned_data = form.cleaned_data
                username = cleaned_data.get('username')
                password = cleaned_data.get('password1')
                first_name = cleaned_data.get('first_name')
                last_name = cleaned_data.get('last_name')
                email = cleaned_data.get('email')
                phone_number = cleaned_data.get('phone_number')
                dni = cleaned_data.get('dni')

                user = User.objects.create_user(username, email, password)

                user.first_name = first_name
                user.last_name = last_name

                user.save()

                employee = Employee()
                employee.user = user
                employee.phone_number = phone_number
                employee.dni = dni

                employee.save()

                messages.success(
                    request, 'You Have Successfully Registered An Employee')

                return redirect('/webprofile')

        else:
            form = RegisterForm()
        context = {
            'form': form
        }

        return render(request, 'Sbike/employee_register.html', context)

    else:
        messages.error(request, 'This Content is Unavailable!')
        return redirect('/webprofile')


# ##-----------------------------------------------------------------------## #
# ##-------------------END--REGISTER--EMPLOYEE-----------------------------## #
# ##-----------------------------------------------------------------------## #
