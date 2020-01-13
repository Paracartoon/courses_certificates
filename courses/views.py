from django.shortcuts import render, get_object_or_404, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.template import loader
from home.models import Tipologia_corso, Corso, Docenti
from home.forms import CorsoForm, DocentiForm, DirettoriForm, Direttori
from django.core.mail import send_mail
from fatture.models import Fatture
from fatture.forms import FattureForm
from attestati.forms import RichestaAttestatiForm
from materiale_didattico.models import MaterialeDidattico
from attestati.models import RichestaAttestati
from tesserini.forms import RichestaTesseriniForm, CorsistaForm
from tesserini.models import RichestaTesserini, Corsista
from impostazioni.forms import ImpostazioniForm
from impostazioni.models import Impostazioni
from django.template.loader import render_to_string
import weasyprint
from weasyprint import HTML, CSS
from django.conf import settings
from impostazioni.models import Impostazioni
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from django.http import JsonResponse
from django.db.models import Q
from django.core import serializers
import locale
import sys
from datetime import datetime



email_list = ['director@some_school.org', 'secretary@some_school.org']


@login_required
def stampare_corsisti(request, id):

	corso = Corso.objects.get(id=id)
	try:
		impostazioni = Impostazioni.objects.get(user=request.user)
	except Impostazioni.DoesNotExist:
		return HttpResponse('Prima di stampare neccessario inserire la firma nella sezione Impostazioni')

	try:
		richiesta = RichestaAttestati.objects.get(numero_corso_field=id, approvata=True)	
		data = json.loads(richiesta.corsisti_field)
		corsisti = []

		for i in range(len(data)):
			corsista = {}
			corsista['nome'] = data[i]['nome']
			corsista['cognome'] = data[i]['cognome']
			corsista['datanascita'] = data[i]['datanascita']
			corsista['sesso'] = data[i]['sesso']
			corsista['cf'] = data[i]['cf']
			corsisti.append(corsista)

		return render(request, 'account/stampare_corsisti.html', {'corso': corso, 'richiesta': richiesta, 'corsisti':corsisti, 'impostazioni':impostazioni})

	except RichestaAttestati.DoesNotExist:
		return HttpResponse('Prima di stampare neccessario approvare la richiesta Attestati')

	except RichestaAttestati.MultipleObjectsReturned:
		richiesta = RichestaAttestati.objects.latest('data_richiesta')

		return render(request, 'account/stampare_corsisti.html', {'corso': corso, 'richiesta': richiesta})



@login_required
def attestato_pdf(request, corsoid, corsistacf):

	corso = Corso.objects.get(id=corsoid)
	logo = corso.logo
	numerocorso = int(corso.id)

	try:
		impostazioni = Impostazioni.objects.get(user=request.user)
	except Impostazioni.DoesNotExist:
		impostazioni = []

	firma = impostazioni.firma_digitale

	try:
		richiesta = RichestaAttestati.objects.get(numero_corso_field=corsoid)
		data = json.loads(richiesta.corsisti_field)
		numero_corsisti = len(data)

		for i in data:

			if 	i['cf'] == corsistacf:
				nome = i['nome']
				cognome = i['cognome']
				if 'birthplace' in i:
					luogo = i['birthplace']
				else:
					luogo = i['birthplace_']
				if 'birthplace_province' in i:
					prov = i['birthplace_province']
				else:
					prov = i['birthplace_province_']
				sesso = i['sesso']
				datanascita = i['datanascita']
				posizione = i['posizione']


		svolgimenti = json.loads(corso.svolgimenti_field)
		lista_sv = []

		for i in svolgimenti:
			giorno = i['inizio']
			ore = i['ora']
			durata = i['durata']
			sv = [giorno, ore, durata]
			lista_sv.append(sv)

		if len(lista_sv) > 4:
			lista_sv = lista_sv[0:4]

		lencorso = len(corso.programma)
		if lencorso > 6625:
			part_one = corso.programma[:6625] 
			part_two = corso.programma[6625:]
		else:
			part_one = corso.programma
			part_two = 0

		html = render_to_string('attestati/attestato.html', 
			{'corso': corso, 'part_one': part_one, 'part_two':part_two, 'lencorso':lencorso, 'richiesta': richiesta, 'firma':firma, 'logo':logo, 
			'datanascita':datanascita, 'nome':nome, 'luogo':luogo, 'cognome':cognome, 'prov':prov, 'posizione':posizione,'sesso':sesso,'svolgimenti':svolgimenti, 
			'lista_sv':lista_sv, 'corsistacf':corsistacf, 'numerocorso':numerocorso, 'numero_corsisti':numero_corsisti})

		response = HttpResponse(content_type='application/pdf')
		response['Content-Disposition'] = 'filename="attestato.pdf"'
		weasyprint.HTML(string=html).write_pdf(response,
			stylesheets=[weasyprint.CSS(
				settings.STATIC_ROOT + 'css/pdf.css')])
		return response
	except RichestaAttestati.DoesNotExist:
		return HttpResponse('Prima di stampare neccessario fare la richiesta Attestati')





@login_required
def lettera_autorizzazione(request, id):

	corso = Corso.objects.get(id=id)
	tipologia = corso.tipologia
	oretotale = tipologia.ore
	ref = tipologia.riferimento_legislativo
	provincia = corso.provincia
	citta = corso.citta
	indirizzo = corso.indirizzo
	cap = corso.cap
	posti = corso.posti
	direttore = corso.direttori
	docente = corso.docenti_names
	data_richiesta = corso.formatedDate()
	protocollo = corso.protocollo
	numero_convenzione = corso.numero_di_convenzione
	data_di_convenzione = corso.data_di_convenzione

	svolgimenti = json.loads(corso.svolgimenti_field)
	lista_sv = []

	for i in svolgimenti:
		giorno = i['inizio']
		ore = i['ora']
		durata = i['durata']
		sv = [giorno, ore, durata]
		lista_sv.append(sv)

	if len(lista_sv) > 4:
		lista_sv = lista_sv[0:4]

	try:
		impostazioni = Impostazioni.objects.get(user=request.user)
		nome_azienda = impostazioni.nome_azienda
		indirizzo1 = impostazioni.indirizzo_1
		indirizzo2 = impostazioni.indirizzo_2

	except Impostazioni.DoesNotExist:
		nome_azienda = 'Nome azienda'
		indirizzo1 = 'via numero civico'
		indirizzo2 = 'cap citta provincia'

	


	html = render_to_string('attestati/la.html', 
		{'tipologia':tipologia, 'oretotale':oretotale, 'indirizzo':indirizzo, 'citta':citta, 'provincia':provincia, 'cap':cap, 'ref':ref, 'direttore':direttore,
		'posti':posti, 'lista_sv':lista_sv, 'docente': docente, 'nome_azienda':nome_azienda, 'indirizzo1':indirizzo1, 'indirizzo2':indirizzo2,
		'data_richiesta':data_richiesta, 'protocollo':protocollo, 'numero_convenzione':numero_convenzione, 'data_di_convenzione':data_di_convenzione})
	response = HttpResponse(content_type='application/pdf')

	response['Content-Disposition'] = 'filename="lettera_di_autorizzazione_corso.pdf"'

	weasyprint.HTML(string=html).write_pdf(response,
		stylesheets=[weasyprint.CSS(
			settings.STATIC_ROOT + 'css/pdf_la.css')])
	return response




@login_required
def anagrafiche(request):

	user = request.user

	fatture = Fatture.objects.filter(user=user.id)
	if fatture:
		numero_fatture = fatture.filter(pagato=False).count()
	else:
		numero_fatture = 0

	corses = Corso.objects.filter(user=user.id)
	corsoids = []
	docenti_table = []

	for i in corses:
		corsoids.append(i.id)
	
	docenti = Docenti.objects.filter(user=user)

	try:
		richieste = RichestaAttestati.objects.filter(numero_corso_field__in=corsoids)
		jsons = []
		corsisti_table = []
		cflist = {}

		for r in richieste:
			jsons.append(json.loads(r.corsisti_field))

		for n in jsons:
			for internal in n:

				corsista = {}
				corsista['nome'] = internal['nome']
				corsista['cognome'] = internal['cognome']
				corsista['sesso'] = internal['sesso']
				corsista['datanascita'] = internal['datanascita']
				corsista['cf'] = internal['cf']

				#corsista['posizione'] = internal['posizione']


				if corsista['cf'] not in cflist:
					cflist[corsista['cf']] = True
					corsisti_table.append(corsista)


		return render(request,
					'account/anagrafiche.html',
					{ 'user':user, 'numero_fatture': numero_fatture, 'docenti': docenti, 'jsons':jsons, 'corsisti_table': corsisti_table})

	except RichestaAttestati.DoesNotExist:

		return render(request,
					'account/anagrafiche.html',
					{ 'user':user, 'numero_fatture': numero_fatture, 'docenti': docenti})




@login_required
def richiestacorso(request):

	tips = Tipologia_corso.objects.all()
	user = request.user
	try:
		impostazioni = Impostazioni.objects.get(user=user)
	except Impostazioni.DoesNotExist:
		return HttpResponse('Prima di effetuare richiesta corso bisogna inserire i dati nella sezione IMPOSTAZIONI')
	docenti = Docenti.objects.filter(user=user)
	impostazioni = Impostazioni.objects.get(user=user)
	numero_di_convenzione = impostazioni.numero_di_convenzione
	data_di_convenzione = impostazioni.data_di_convenzione
	direttore = user.first_name+' '+user.last_name

	fatture = Fatture.objects.filter(user=user.id)

	if request.method == 'POST':

		form = CorsoForm(request.POST, request.FILES, user=request.user)

		if form.is_valid():


			new_form = form.save()
			new_form.user = request.user
			new_form.save()
			message = form.cleaned_data['tipologia']
			numero_corso = str(new_form.id)
			docenti_corso = form.cleaned_data['docenti']
			docenti_ids = []

			qs = serializers.serialize('json', docenti_corso)
			qqs = json.loads(qs)

			for i in qqs:
				doc = Docenti.objects.get(id=i["pk"])
				docenti_ids.append(i["pk"])
				corsi_dict = doc.corsi_docente.split(",")
				corsi_dict.append(numero_corso)
				str1 = ','.join(corsi_dict)
				doc.corsi_docente = str1
				doc.save()

			new_form.docenti = docenti_ids
			new_form.save()



			send_mail('Nuova richiesta corso da edafil.org', 
				'Ricevuta nuova richiesta svolgimento corso in '+ str(message)+', dall`utente '+str(user.first_name)+' '+str(user.last_name)+
				'\nPer controllare i dati accedi /admin', 
				'noreply@some_school.org', email_list, fail_silently=False)
			return HttpResponseRedirect('/grazie?protocollo='+str(new_form.id))
		else:
			return render(request, 'home/index.html', {'tips': tips, 'form': form, 'docenti': docenti, 'user':user, 'fatture':fatture, 'numero_fatture': numero_fatture, 
				'direttore':direttore, 'numero_di_convenzione': numero_di_convenzione, 'data_di_convenzione':data_di_convenzione})

	else:
		form = CorsoForm(user=request.user)

	return render(request, 'home/index.html', {'tips': tips, 'form': form, 'docenti': docenti, 'user':user, 'fatture':fatture, 'numero_fatture': numero_fatture, 
		'direttore':direttore, 'numero_di_convenzione': numero_di_convenzione, 'data_di_convenzione':data_di_convenzione})





def aggiungi_docente(request):

	user = request.user
	docenti = Docenti.objects.filter(user=user)
	if request.method == 'POST':

		form = DocentiForm(request.POST, request.FILES)

		try:
			new_docent = docenti.get(nome_cognome=form.data['nome_cognome'])

			response = {}
			response['value'] = 0
			response['name'] = form.data['nome_cognome']
			return JsonResponse(response)

		except Docenti.DoesNotExist:

			new_form = form.save()
			response = {}
			response['value'] = new_form.id
			response['name'] = new_form.nome_cognome


			return JsonResponse(response)

		except Docenti.MultipleObjectsReturned:
			response = {}
			response['value'] = 0
			response['name'] = form.data['nome_cognome']
			return JsonResponse(response)


@login_required
def modifica_docente(request, id):

	user = request.user
	try:
		docente = Docenti.objects.get(id=id)
		form = DocentiForm(instance=docente)


		if request.method == 'POST':

			form = DocentiForm(request.POST, request.FILES, instance=docente)

			if form.is_valid():

				new_form = form.save()
				new_form.user = user
				new_form.save()
			
				send_mail('Modifica dati docente', 
				'L`utente '+str(user.first_name)+' '+str(user.last_name)+' ha modificato i dati docente '+str(docente.nome_cognome)+
				'\nPer controllare i dati accedi: http://edafil.org/admin/home/docenti/', 
				'noreply@some_school.org', email_list, fail_silently=False)
				return HttpResponseRedirect('/account/anagrafiche')
			else:

				return render(request,
						'account/modifica_docente.html',
						{ 'user':user, 'form': form})

		else:
			form = DocentiForm(instance=docente)

		return render(request,
						'account/modifica_docente.html',
						{ 'user':user, 'form': form})

	except Docenti.DoesNotExist:
		return HttpResponse('Docente non trovato')


def cancellare_docente(request):

	item = Docenti.objects.get(id=request.GET['delete'])
	item.delete()

	return HttpResponse('OK')
		
	
def aggiungi_direttore(request):

	if request.method == 'POST':

		form = DirettoriForm(request.POST, request.FILES)
		new_form_direttore = form.save()
		response = {}
		response['value'] = new_form_direttore.id
		response['name'] = new_form_direttore.nome_cognome_direttore


		return JsonResponse(response)




@login_required
def bound_form(request, id):

	item = get_object_or_404(Corso, id=id)
	user = request.user
	data_oggi_correct = datetime.now()
	data_inizio_corso_correct = datetime.strptime(item.data_inizio, '%d-%m-%Y')

	if data_inizio_corso_correct <= data_oggi_correct:
		return HttpResponse('Non si puo modificare il corso gia iniziato')
	form = CorsoForm(instance=item)

	docenti = Docenti.objects.filter(user=user)
	direttore = user.first_name+' '+user.last_name

	try:
		impostazioni = Impostazioni.objects.get(user=user)
	except Impostazioni.DoesNotExist:
		return HttpResponse('Prima di effetuare richiesta corso bisogna inserire i dati nella sezione IMPOSTAZIONI')

	impostazioni = Impostazioni.objects.get(user=user)
	numero_di_convenzione = impostazioni.numero_di_convenzione
	data_di_convenzione = impostazioni.data_di_convenzione

	tips = Tipologia_corso.objects.all()
	selected_docents = []
	for d in docenti:

		if str(int(id)) in d.corsi_docente:

			selected_docents.append(d.nome_cognome)
	if item.convalidato == True:
		modifica = 'non si puo'
	else:
		modifica = 'ok'


	if request.method == 'POST':
		
		form = CorsoForm(request.POST, request.FILES, instance=item, user=request.user)
		item.richiesta_modifica = True
		item.autorizzato = None
		item.richiesta_modifica_corso = "In attesa di approvazione"

		if form.is_valid():

			new_form = form.save()
			new_form.user = request.user
			new_form.save()
			message = form.cleaned_data['tipologia']
			numero_corso = str(new_form.id)
			protocollo = str(new_form.protocollo)
			docenti_corso = form.cleaned_data['docenti']
			docenti_ids = []
			qs = serializers.serialize('json', docenti_corso)
			qqs = json.loads(qs)

			for i in qqs:
				doc = Docenti.objects.get(id=i["pk"])
				docenti_ids.append(i["pk"])
				corsi_dict = doc.corsi_docente.split(",")
				corsi_dict.append(numero_corso)
				str1 = ','.join(corsi_dict)
				doc.corsi_docente = str1
				doc.save()

			new_form.docenti = docenti_ids
			new_form.save()

			send_mail('Nuova richiesta modifica corso', 'Ricevuta nuova richiesta modifica corso in '+ 
				str(message)+', protocollo '+protocollo+', dall utente '+str(user.first_name)+' '+str(user.last_name)+
				'\nPer controllare i dati accedi /admin', 
				'noreply@some_school.org', email_list, fail_silently=False)
			return HttpResponseRedirect('/grazie_modifica')
		else:
			return HttpResponse('Si prega di verificare i dati inseriti')

	else:
		form = CorsoForm(instance=item, user=request.user)

	return render(request, 'home/index.html', {'numero_di_convenzione': numero_di_convenzione, 'data_di_convenzione':data_di_convenzione, 
		'modifica': modifica, 'tips': tips, 'form': form, 'docenti': docenti, 'user':user, 'direttore':direttore, 'selected_docents': selected_docents})


@login_required
def richiesta_attestati(request, id):

	user = request.user
	item = Corso.objects.get(id=id)
	posti = item.posti
	protocollo = item.protocollo

	corsoid = id

	try:
		ritem = RichestaAttestati.objects.get(numero_corso_field=id)
		form = RichestaAttestatiForm(instance=ritem)
		current_richiesta_corsisti = json.loads(ritem.corsisti_field)
		current_richiesta_corsisti_cf = {}
		for i in current_richiesta_corsisti:
			current_richiesta_corsisti_cf[i['cf']] = True


		if ritem.approvata == False or ritem.approvata == None:
			modifica = 'si'
			corses = Corso.objects.filter(user=user.id)
			corsoids = []

			for i in corses:
				corsoids.append(i.id)

			try:
				richieste = RichestaAttestati.objects.filter(numero_corso_field__in=corsoids)
				jsons = []
				corsisti_table = []
				cflist = {}

				for r in richieste:
					jsons.append(json.loads(r.corsisti_field))

				for n in jsons:
					for internal in n:

						corsista = {}
						corsista['nome'] = internal['nome']
						corsista['cognome'] = internal['cognome']
						corsista['sesso'] = internal['sesso']
						corsista['datanascita'] = internal['datanascita']
						corsista['cf'] = internal['cf']
						if 'birthplace_' in internal:
							corsista['provincia'] = internal['birthplace_province_']
							corsista['luogo'] = internal['birthplace_']
						else:
							corsista['provincia'] = internal['birthplace_province']
							corsista['luogo'] = internal['birthplace']

						#corsista['posizione'] = internal['posizione']

						if corsista['cf'] not in cflist and corsista['cf'] not in current_richiesta_corsisti_cf:
							cflist[corsista['cf']] = True
							corsisti_table.append(corsista)

			except RichestaAttestati.DoesNotExist:
				corsisti_table = []


			if request.method == 'POST':

				form = RichestaAttestatiForm(request.POST, request.FILES, instance=ritem)

				if form.is_valid():

					numero_corso_field = int(form.cleaned_data['numero_corso_field'])
					richieste_effetuate = RichestaAttestati.objects.filter(numero_corso_field = numero_corso_field)
					new_form = form.save()
					new_form.user = str(user.first_name)+' '+str(user.last_name)
					new_form.protocollo = int(protocollo)
					corsisti_test = json.loads(form.cleaned_data['corsisti_field']);
					corsisti = []

					for i in range(len(corsisti_test)):
						if corsisti_test[i] is not None:
							corsisti.append(corsisti_test[i])


					for cfcheck in corsisti:	
						if cfcheck['cf'] == '':

							return HttpResponse('Si prega di controllare i codici fiscali inseriti')

						elif ' ' in cfcheck['cf']:

							return HttpResponse('Si prega di controllare i codici fiscali inseriti, ci sono spazi vuoti')


					new_form = form.save()
					new_form.corsisti_field = json.dumps(corsisti)
					new_form.save()

					send_mail('Nuova richiesta modifica attestati', 
						'Ricevuta nuova modifica attestati per corso numero '+ str(protocollo)+' dell`utente '+str(user.first_name)+' '+str(user.last_name)+'.'+ 
						'\nPer controllare i dati accedi admin', 'noreply@some_school.org', 
						email_list, fail_silently=False)
					return HttpResponseRedirect('/grazie_attestati')

			else:
				form = RichestaAttestatiForm(instance=ritem)
				return render(request, 'home/richiesta_attestati_modifica.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 
					'modifica':modifica, 'protocollo':protocollo, 'posti':posti, 'ritem':ritem, 'corsisti_table':corsisti_table})


		elif ritem.approvata == True:

			return HttpResponse('Richiesta gia approvata')


		return render(request, 'home/richiesta_attestati.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 
			'modifica':modifica, 'protocollo':protocollo, 'posti':posti, 'corsisti_table':corsisti_table})


	except RichestaAttestati.DoesNotExist:


		modifica = 'no'
		corses = Corso.objects.filter(user=user.id)
		corsoids = []
			
		for i in corses:
			corsoids.append(i.id)


		try:
			richieste = RichestaAttestati.objects.filter(numero_corso_field__in=corsoids)
			jsons = []
			corsisti_table = []
			cflist = {}

			for r in richieste:
				jsons.append(json.loads(r.corsisti_field))

			for n in jsons:
				for internal in n:

					corsista = {}
					corsista['nome'] = internal['nome']
					corsista['cognome'] = internal['cognome']
					corsista['sesso'] = internal['sesso']
					corsista['datanascita'] = internal['datanascita']
					corsista['cf'] = internal['cf']
					print('************', internal)
					if 'birthplace_' in internal:
						corsista['provincia'] = internal['birthplace_province_']
						corsista['luogo'] = internal['birthplace_']
					else:
						corsista['provincia'] = internal['birthplace_province']
						corsista['luogo'] = internal['birthplace']

					#corsista['posizione'] = internal['posizione']

					if corsista['cf'] not in cflist:
						cflist[corsista['cf']] = True
						corsisti_table.append(corsista)

		except RichestaAttestati.DoesNotExist:
			corsisti_table = []

		


		if request.method == 'POST':
			item.richiesta_rilascio_attestati = True
			item.richiesta_attestati = 'In attesa di approvazione nella sezione Attestati -- Richieste'
			item.save()
			form = RichestaAttestatiForm(request.POST, request.FILES)

			if form.is_valid():

				numero_corso_field = int(form.cleaned_data['numero_corso_field'])
				richieste_effetuate = RichestaAttestati.objects.filter(numero_corso_field = numero_corso_field)
				corsisti_test = json.loads(form.cleaned_data['corsisti_field']);
				corsisti = []

				for i in range(len(corsisti_test)):
					if corsisti_test[i] is not None:
						corsisti.append(corsisti_test[i])
	

				for cfcheck in corsisti:	
					if cfcheck['cf'] == '':

						return HttpResponse('Si prega di controllare i codici fiscali inseriti')

					elif ' ' in cfcheck['cf']:

						return HttpResponse('Si prega di controllare i codici fiscali inseriti, ci sono spazi vuoti')

				new_form = form.save()
				new_form.corsisti_field = json.dumps(corsisti)
				new_form.save()
				new_form.user = str(user.first_name)+' '+str(user.last_name)
				new_form.protocollo = int(protocollo)
				new_form.save()

				send_mail('Nuova richiesta rilascio attestati', 
					'Ricevuta nuova richiesta rilascio attestati per corso numero '+ str(protocollo)+' dell`utente '+str(user.first_name)+' '+str(user.last_name)+'.'+ 
					'\nPer controllare i dati accedi admin', 'noreply@some_school.org', 
					email_list, fail_silently=False)
				return HttpResponseRedirect('/grazie_attestati')
			else:
				return render(request, 'home/richiesta_attestati.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 
			'modifica':modifica, 'protocollo':protocollo, 'posti':posti, 'corsisti_table':corsisti_table})

		else:
			form = RichestaAttestatiForm()

		return render(request, 'home/richiesta_attestati.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 
			'modifica':modifica, 'protocollo':protocollo, 'posti':posti, 'corsisti_table':corsisti_table})



def anulla_corso(request):
	item = get_object_or_404(Corso, id=request.GET['delete'])
	item.delete()

	return HttpResponse('OK')



@login_required
def richiesta_tesserini(request, id):

	user = request.user
	item = get_object_or_404(Corso, id=id)
	numero_protocollo = int(id)
	protocollo = item.protocollo
	corsoid = id
	corsistijq = []

	try:
		richiesta = RichestaAttestati.objects.get(numero_corso_field=id, approvata=True)	
		data = json.loads(richiesta.corsisti_field)
		
		for i in range(len(data)):
			corsistijq.append(data[i]['nome']+' '+data[i]['cognome'])
		
	except RichestaAttestati.DoesNotExist:
		pass

	except RichestaAttestati.MultipleObjectsReturned:
		richiesta = RichestaAttestati.objects.latest('data_richiesta')	
		data = json.loads(richiesta.corsisti_field)

		for i in range(len(data)):
			
			corsistijq.append(data[i]['nome']+' '+data[i]['cognome'])

	if request.method == 'POST':
		form = RichestaTesseriniForm(request.POST, request.FILES)
		if form.is_valid():
			numero_corso_field = int(form.cleaned_data['numero_corso_field'])
			new_form = form.save()
			new_form.user = str(user.first_name)+' '+str(user.last_name)
			new_form.protocollo = int(protocollo)
			new_form.save()
			corsisti = Corsista.objects.filter(corsoid=numero_corso_field)

			for i in corsisti:
				i.richiesta_tesserini = new_form
				i.save()

			send_mail('Nuova richiesta rilascio tesserini', 
				'Ricevuta nuova richiesta rilascio tesserini per corso numero protocollo '+ str(protocollo)+' dell`utente '+str(user.first_name)+' '+str(user.last_name)+'.'+ 
				'\nPer controllare i dati accedi /admin', 'noreply@some_school.org', 
				email_list, fail_silently=False)
			return HttpResponseRedirect('/grazie_tesserini')
		else:
			return render(request, 'home/richiesta_tesserini.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 'corsistijq':corsistijq,
		'protocollo':protocollo})

	else:
		form = RichestaTesseriniForm()

	return render(request, 'home/richiesta_tesserini.html', {'form': form, 'user':user, 'numero_fatture': numero_fatture, 'corsoid': corsoid, 'corsistijq':corsistijq,
		'protocollo':protocollo})



def aggiungi_corsista(request):

	if request.method == 'POST':

		form = CorsistaForm(request.POST, request.FILES)
		corsoid = int(form.data['corsoid'])
		new_form = form.save()
		response = {}
		response['value'] = new_form.id
		response['name'] = new_form.nome_cognome


		return JsonResponse(response)



@login_required
def dashboard(request):

	user = request.user
	corses = Corso.objects.filter(user=user.id).order_by('-id').exclude(anullato=True)
	corses_atteso_autorizzazione = Corso.objects.filter(Q(autorizzato=False, user=user.id) |
                                       Q(autorizzato=None, user=user.id)).order_by('-id')

	corses_autorizzato = corses.filter(user=user.id, autorizzato=True, richiesta_rilascio_attestati=False).order_by('-id').exclude(convalidato=True)
	corses_richiesta_modifica = corses.filter(user=user.id, richiesta_modifica=True).order_by('-id')
	corses_richiesta_rilascio_attestati = corses.filter(user=user.id, richiesta_rilascio_attestati=True).order_by('-id').exclude(convalidato=True)
	corses_convalidato = corses.filter(user=user.id, convalidato=True).order_by('-id')


	fatture = Fatture.objects.filter(user=user.id)
	if fatture:
		numero_fatture = fatture.filter(pagato=False).count()
	else:
		numero_fatture = -1


	return render(request,
					'account/dashboard.html',
					{'section': 'dashboard', 'corses':corses, 'user':user, 'numero_fatture': numero_fatture, 'corses_atteso_autorizzazione': corses_atteso_autorizzazione,
	'corses_autorizzato': corses_autorizzato, 'corses_richiesta_modifica': corses_richiesta_modifica, 'corses_richiesta_rilascio_attestati': corses_richiesta_rilascio_attestati,
	'corses_convalidato': corses_convalidato, 'extra_dropdowns':extra_dropdowns})




@login_required
def impostazioni(request):

	user = request.user
	#profile = get_object_or_404(Profile, user=user.id)

	fatture = Fatture.objects.filter(user=user.id)
	if fatture:
		numero_fatture = fatture.filter(pagato=False).count()
	else:
		numero_fatture = 0


	try:
		impostazioni = Impostazioni.objects.get(user=user.id)
		form = ImpostazioniForm(instance=impostazioni)


		if request.method == 'POST':
			form = ImpostazioniForm(request.POST, request.FILES, instance=impostazioni, user=request.user)
			if form.is_valid():
				form.save()	
				return HttpResponseRedirect('/account/impostazioni')
			else:
				return render(request,
						'account/impostazioni.html',
						{ 'user':user, 'numero_fatture': numero_fatture, 'form': form})

		else:
			form = ImpostazioniForm(instance=impostazioni, user=request.user)

		return render(request,
						'account/impostazioni.html',
						{ 'user':user, 'numero_fatture': numero_fatture, 'form': form})

	except Impostazioni.DoesNotExist:
		

		if request.method == 'POST':
			form = ImpostazioniForm(request.POST, request.FILES, user=request.user)

			if form.is_valid():

				new_form = form.save()
				new_form.user = request.user
				new_form.save()
				
				return HttpResponseRedirect('/account/impostazioni')
			else:
				return render(request,
						'account/impostazioni.html',
						{ 'user':user, 'numero_fatture': numero_fatture, 'form': form})

		else:
			form = ImpostazioniForm()

		return render(request,
						'account/impostazioni.html',
						{ 'user':user, 'numero_fatture': numero_fatture, 'form': form})





@login_required
def fatture(request):

	user = request.user
	fatture = Fatture.objects.filter(user=user.id)
	non_pagati = fatture.filter(pagato=False)
	importo_totale = ''
	numero = ''
	felenco = []

	if fatture:
		numero_fatture = int(non_pagati.count())
		if non_pagati:

			url = 'https://api.fatture:443/v1/fatture/dettagli'
			for f in range(len(non_pagati)):
				
				if non_pagati[f].token == '':
					importo_totale = 'La fattura non esiste su Fatture in Cloud'
					numero = 'La fattura non esiste su Fatture in Cloud'
				else:
					token = non_pagati[f].token
					fic_id = non_pagati[f].fic_id				

					fattura_data = {
						  "api_uid": "00000",
						  "api_key": "0000000",
						  "id": fic_id,
						  "token": token
						}

					msg = json.dumps(fattura_data).encode('utf8')

					req = Request(url, data=msg,
								headers={'content-type': 'application/json'})
					response = urlopen(req)
					inform = response.read().decode()
					code = response.getcode()
					info = json.loads(inform)

					try: 
						importo_totale = info['dettagli_documento']['importo_totale']+' EUR'
						numero = info['dettagli_documento']['numero']
					except KeyError:
						importo_totale = info['error']
						numero = info['error']

				felenco.append([non_pagati[f].id, numero, importo_totale, non_pagati[f].data, non_pagati[f].corso, non_pagati[f].corso.tipologia])
					
				 
	else:
		numero_fatture = 0

	if request.method == 'POST':

		id = int(request.POST.get('fattura_id'))
		item = get_object_or_404(Fatture, id=id)
		form = FattureForm(request.POST, request.FILES, instance=item)

		if form.is_valid():
			if len(request.FILES) != 0:
				form.save()

				send_mail('Ricevuta conferma pagamento', 'Ricevuta conferma pagamento dal utente: '+str(user)+
					'. \nPer controllare i dati accedi /admin/fatture/', 
					'noreply@some_school.org', email_list, fail_silently=False)
				item.ricevuta_caricata = True
				item.save()
				return render(request, 'home/grazie_fatture.html')
			else:
				return HttpResponse('Nessun file allegato')
		else:
			return render(request,
					'account/fatture.html',
					{'section': 'dashboard', 'user':user, 'fatture':fatture, 'numero_fatture': numero_fatture})

	else:
		form = FattureForm()

	return render(request,
					'account/fatture.html',
					{'section': 'dashboard', 'user':user, 'fatture':fatture, 'numero_fatture': numero_fatture, 'form':form})