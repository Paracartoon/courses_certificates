from django.db import models
from django.utils import timezone
import datetime
from tinymce.models import HTMLField
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib import admin
from django.template.defaultfilters import truncatechars
from django.utils.safestring import mark_safe
from django.core.mail import send_mail
from django.http import HttpResponse
from django.apps import apps
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMessage
import os
from django.core.validators import int_list_validator
from uuid import uuid4
from io import BytesIO
from django.template.loader import render_to_string
import weasyprint
from weasyprint import HTML, CSS
from django.conf import settings
from impostazioni.models import Impostazioni
import json





User = get_user_model()


def path_and_rename(instance, filename):

    upload_to = 'uploads/'
    ext = filename.split('.')[-1]
    filename = '{}.{}'.format(uuid4().hex, ext)
    return os.path.join(upload_to, filename)


class Tipologia_corso(models.Model):
	tipologia = models.CharField(max_length=300)
	descrizione = models.TextField(null=True)
	riferimento_legislativo = models.TextField(max_length=1000, default="", null=True)
	programma = HTMLField(default="Inserire programma per questo corso", null=True)
	ore = models.IntegerField(default=0)

	def __str__(self):
		return self.tipologia

	class Meta:
		verbose_name_plural = "Tipologie di corsi (programma, riferimento legislativo, descrizione)"
		verbose_name = "Tipologia corso"


class Tipologia_corsoAdmin(admin.ModelAdmin):
	
	list_display = ('tipologia', 'ore', 'descrizione', 'riferimento_legislativo')



class Categoria(models.Model):
	categoria = models.CharField(max_length=300, blank=True)

	def __str__(self):
		return self.categoria

	class Meta:
		verbose_name_plural = "Categorie"
		verbose_name = "Categoria"


class Attivita(models.Model):
	attivita = models.CharField(max_length=300, blank=True)

	def __str__(self):
		return self.attivita

	class Meta:
		verbose_name_plural = "Attivita"
		verbose_name = "Attivita"



class Docenti(models.Model):
	nome_cognome = models.CharField(max_length=300, null=True)
	curriculum = models.FileField(upload_to=path_and_rename, null=True)
	autocertificazione = models.FileField(upload_to=path_and_rename, null=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
	corsi_docente = models.CharField(max_length=30000, default='0000', null=True)

	def __str__(self):
		return self.nome_cognome

	class Meta:
		verbose_name_plural = "Docenti"
		verbose_name = "Docente"

class DocentiAdmin(admin.ModelAdmin):

	
	list_display = ('nome_cognome', 'user', 'curriculum', 'autocertificazione')
	fields = ('nome_cognome', 'curriculum', 'autocertificazione', 'user', 'corsi_docente')




class Direttori(models.Model):
	nome_cognome_direttore = models.CharField(max_length=300, blank=True, null=True)
	curriculum_direttore = models.FileField(upload_to=path_and_rename, null=True, blank=True)
	user_direttore = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

	def __str__(self):
		return str(self.nome_cognome_direttore)

	class Meta:
		verbose_name_plural = "Direttori"
		verbose_name = "Direttore"


class DirettoriAdmin(admin.ModelAdmin):

	
	list_display = ('nome_cognome_direttore', 'user_direttore')
	fields = ('nome_cognome_direttore', 'curriculum_direttore', 'user_direttore')
	readonly_fields = ('nome_cognome_direttore', 'curriculum_direttore', 'user_direttore')




class Corso(models.Model):



	tipologia = models.ForeignKey('Tipologia_corso', on_delete=models.CASCADE, null=True)
	NUMCHOICES = [(i,i) for i in range(100)]
	posti = models.IntegerField(choices=NUMCHOICES, null=True)
	categoria = models.ForeignKey('Categoria', on_delete=models.CASCADE, default=1, null=True)
	attivita = models.ForeignKey('Attivita', on_delete=models.CASCADE, default=1, null=True, blank=True)
	logo = models.FileField(upload_to=path_and_rename, null=True, blank=True)
	indirizzo = models.CharField(max_length=300, null=True)
	citta = models.CharField(max_length=300, null=True)

	PROV = (
		('AG', 'AG'), ('AL', 'AL'), ('AN', 'AN'), ('AO', 'AO'), ('AQ', 'AQ'), ('AR', 'AR'), ('AP', 'AP'), 
		('AT', 'AT'), ('AV', 'AV'), ('BA', 'BA'), ('BT', 'BT'), ('BL', 'BL'), ('BN', 'BN'), ('BG', 'BG'), 
		('BI', 'BI'), ('BO', 'BO')
		)
    

	provincia = models.CharField(max_length=10, choices=PROV, default='AG', null=True)
	cap = models.CharField(max_length=10, null=True)
	docenti = models.CharField(max_length=1000, null=True)
	direttori = models.CharField(max_length=3000, null=True)
	numero_di_convenzione = models.CharField(max_length=300, null=True)
	data_di_convenzione = models.CharField(max_length=300, null=True)	
	data_inizio =models.CharField(max_length=300, null=True)
	data_fine = models.CharField(max_length=300, null=True)
	svolgimenti_field = models.CharField(max_length=100000, null=True)
	in_bozza = models.BooleanField(default=False, null=True)
	atteso_autorizzazione = models.BooleanField(default=True, null=True)
	autorizzato = models.BooleanField(default=None, null=True, help_text="Nel caso di 'SI' dopo click su 'SALVA' il sistema mandera email all`utente con la conferma di richiesta/modifica")
	perche_non_autorizzato = models.TextField(null=True, blank=True, help_text="Nel caso di corso respinto (non autorizzato), mettere spiegazioni qui. Dopo il click su 'SALVA' il sistema mandera email all`utente con questi spiegazioni")
	#richiesta_modifica = models.BooleanField(default=False, null=True)
	richiesta_modifica = models.BooleanField(default=False, null=True)
	richiesta_rilascio_attestati = models.BooleanField(default=False, null=True)
	richiesta_attestati = models.CharField(max_length=100000, null=True, default="Non effetuata")
	richiesta_modifica_corso = models.CharField(max_length=100000, null=True, default="Non effetuata")
	convalidato = models.BooleanField(default=None, null=True)
	perche_non_convalidato = models.TextField(null=True, blank=True, help_text="Nel caso di corso respinto (non convalidato), mettere spiegazioni qui. Dopo il click su 'SALVA' il sistema mandera email all`utente con questi spiegazioni")
	anullato = models.BooleanField(default=False, null=True)
	user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
	programma = models.TextField(null=True)
	lettera_autorizzazione = models.FileField(upload_to=path_and_rename, null=True, blank=True)
	data_richiesta = models.DateField(("Data di richiesta"), default=datetime.date.today)
	fattura_pagata = models.BooleanField(default=False, null = True)
	protocollo = models.IntegerField(default=0)

	@property
	def short_description(self):
		return truncatechars(self.tipologia, 100) +' Protocollo # '+ str(self.protocollo)

	@mark_safe
	def logo_img(self):
		return f'<img src="{self.logo.url}" width="100"/>' if self.logo else ''
	logo_img.short_description = 'Logo'
	logo_img.allow_tags = True

	def formatedDate(self):

		return self.data_richiesta.strftime("%d/%m/%Y")

	def increment_protocol(self):

		corsi_autorizzati = Corso.objects.filter(autorizzato=True).order_by('-protocollo')
		last_autorizzato = corsi_autorizzati[0]
		new_protocol = last_autorizzato.protocollo+1

		return new_protocol


	def docenti_names(self):
		listad = []
		docenti_list = self.docenti[1:-1].split(",")
		for x in docenti_list:
			d = Docenti.objects.get(id=x.strip())
			listad.append(d.nome_cognome)
		strd = ', '.join(listad)

		return strd


	def __str__(self):
		return str(self.short_description)


	class Meta:
		verbose_name_plural = "AMMINISTRAZIONE CORSI"
		verbose_name = "CORSO"




class CorsoAdmin(admin.ModelAdmin):

	
	exclude = ('in_bozza', 'atteso_autorizzazione', 'richiesta_rilascio_attestati', 'richiesta_modifica')
	list_display = ('short_description', 'data_richiesta', 'logo_img', 'data_inizio', 'data_fine', 'citta', 
		'autorizzato', 'richiesta_modifica_corso', 'richiesta_attestati', 'convalidato', 'direttori', 'numero_di_convenzione', 'fattura_pagata')
	list_filter = ('autorizzato', 'convalidato', 'user', 'data_richiesta')
	fields = ('tipologia', 'logo_img', 'user', 'data_richiesta',  'data_inizio', 'data_fine', 'svolgimenti_field', 'posti', 'programma','categoria', 'attivita',  
		'indirizzo', 'citta', 'provincia', 'cap', 'docenti_names', 'direttori', 'numero_di_convenzione', 'data_di_convenzione', 'richiesta_modifica_corso', 'autorizzato', 
		'perche_non_autorizzato','richiesta_attestati', 'convalidato', 'perche_non_convalidato', 'fattura_pagata', 'protocollo', 'anullato')
	list_display_links = ('logo_img','short_description',)
	readonly_fields = ('tipologia', 'user', 'data_richiesta',  'data_inizio', 'data_fine', 'posti', 'programma','categoria', 'attivita', 'logo_img', 'indirizzo', 'citta', 'cap',  'docenti_names', 'direttori',  'richiesta_attestati', 'richiesta_modifica_corso', 'numero_di_convenzione', 'data_di_convenzione', 'fattura_pagata', 
		'protocollo')



	def save_model(self, request, obj, form, change):


		print(obj.user, form.changed_data)
		for i in form.changed_data:
			if i == 'autorizzato':
				if obj.autorizzato == True:

					if obj.protocollo == 0:

						obj.protocollo = obj.increment_protocol()

					corso = Corso.objects.get(id=obj.id)
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
					protocollo = obj.protocollo
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
						impostazioni = Impostazioni.objects.get(user=corso.user)
						nome_azienda = impostazioni.nome_azienda
						indirizzo1 = impostazioni.indirizzo_1
						indirizzo2 = impostazioni.indirizzo_2

					except Impostazioni.DoesNotExist:
						nome_azienda = 'Nome azienda'
						indirizzo1 = 'via numero civico'
						indirizzo2 = 'cap citta provincia'



					html = render_to_string('attestati/la.html', {'tipologia':tipologia, 'oretotale':oretotale, 'indirizzo':indirizzo, 'citta':citta, 'provincia':provincia, 'cap':cap, 'ref':ref, 'direttore':direttore,
						'posti':posti, 'lista_sv':lista_sv, 'docente': docente, 'nome_azienda':nome_azienda, 'indirizzo1':indirizzo1, 'indirizzo2':indirizzo2,
						'data_richiesta':data_richiesta, 'protocollo':protocollo, 'numero_convenzione':numero_convenzione, 'data_di_convenzione':data_di_convenzione})

					out = BytesIO()
					
					weasyprint.HTML(string=html).write_pdf(out,
						stylesheets=[weasyprint.CSS(
							settings.STATIC_ROOT + 'css/pdf_la.css')])


					obj.richiesta_modifica = False
					obj.richiesta_modifica_corso = 'OK'

					super().save_model(request, obj, form, change)

					msg = EmailMessage('Corso autorizzato', 'Egregio Convenzionato, Le comunichiamo di aver autorizzato lo svolgimento del seguente corso in aula: '+str(obj.tipologia)+', protocollo numero '+str(obj.protocollo)+'.\nIn allegato trasmettiamo il PDF della lettera di autorizzazione', 'noreply@some_school.org', 
						[obj.user.email, 'secretary@some_school.org'])

					
					msg.attach('lettera_di_autorizzazione_corso_{}.pdf'.format(obj.protocollo), out.getvalue(), 'application/pdf') #("certificate.pdf", pdf, "application/pdf")

					print('before')
					msg.send(fail_silently=not(settings.DEBUG))
					print('after')
				


				if obj.autorizzato == False:

					if obj.perche_non_autorizzato:
						messagge = str(obj.perche_non_autorizzato)
					else:
						messagge = 'Nessun motivo indicato'

					send_mail('Richiesta corso respinta', 
					'Egregio Convenzionato, Le comunichiamo di aver respinto la richiesta svolgimento corso : '+str(obj.tipologia)+' Il motivo: '+messagge, 
					'noreply@some_school.org', 
					[obj.user.email], fail_silently=False)

			if i == 'convalidato':

				if obj.convalidato == True:

					rmodel = apps.get_model('attestati', 'RichestaAttestati')
					try:
						richiesta = rmodel.objects.get(numero_corso_field=obj.id)

						if richiesta.approvata == True:

							obj.richiesta_modifica = False
							obj.autorizzato == True
							obj.richiesta_modifica_corso = 'Approvata o non effetuata'
							obj.richiesta_attestati = 'Approvata' 
							send_mail('Corso convalidato', 
								'Egregio Convenzionato, Le comunichiamo di aver convalidato seguente corso in aula: '+str(obj.tipologia), 'noreply@some_school.org', 
								[obj.user.email], fail_silently=False)
						else:
							obj.convalidato = None
							messages.add_message(request, messages.INFO, 'Prima neccessario approvare la richiesta Attestati nella sezione Attestati -> Richiesta')
					except ObjectDoesNotExist:
						obj.convalidato = None
						messages.add_message(request, messages.INFO, 'Prima neccessario approvare la richiesta Attestati nella sezione Attestati -> Richiesta')



				if obj.convalidato == False:

					if obj.perche_non_convalidato:
						messagge = str(obj.perche_non_convalidato)
					else:
						messagge = 'Nessun motivo indicato'

					send_mail('Corso non convalidato', 
					'Egregio Convenzionato, Le comunichiamo di aver respinto la richiesta convalidazione corso : '+str(obj.tipologia)+'Il motivo: '+messagge, 
					'noreply@some_school.org', 
					[obj.user.email], fail_silently=False)



		super().save_model(request, obj, form, change)

