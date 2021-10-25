import discord
from discord.ext import commands
import time
import asyncio

client = commands.Bot("$") #El 'prefix' del bot. Va a leer cualquier mensaje que empieze con este caracter como un posible comando.

class Pregunta:
    def __init__(self, preg, resp):
        self.preg = preg
        self.resp = resp

#El texto de cada pregunta, include las preguntas en si y las posibles respuestas. "\n" simboliza una nueva linea.
#Las preguntas se dividen por comas.
text_preguntas = [
    "Las naranjas son de color naranja?\n(a) Si\n(b) No",
    "Cuanto es 5*5?\n(a) 20\n(b) 30\n(c) 25",
    "Que significa \\n en codigo?\n(a) Cancela\n(b) Nueva Linea\n(c) No significa nada"
    ]

#En este segmento se determina la respuesta de cada pregunta. Por ejemplo, la respuesta a la segunda pregunta es "c".
preguntas = [
    Pregunta(text_preguntas[0], "a"),
    Pregunta(text_preguntas[1], "c"),
    Pregunta(text_preguntas[2], "b"),
    ]

@client.event#Cuando el bot inicializa.
async def on_ready():
    print('---Bot de Evaluacion iniciado---')
    print("Loggeado como: {}".format(client.user.name))
    
    #Esta linea cambia el "Status" del bot en discord. Es opcional y se puede borrar si no se desea...
    #...pero por lo general yo la uso para recordarle a los usuarios cual es el "Prefix"
    await client.change_presence(activity=discord.Game(name="Usar $examen"))

@commands.cooldown(1, 30, commands.BucketType.user)
@client.command()       #Aca empieza el comando de $examen, si necesitas cambiar el comando en algun momento,
async def examen(ctx):  #simplemente podes cambiar "async def examen(ctx)" por "async def ejemplo(ctx)"  
    
    if isinstance(ctx.channel, discord.channel.DMChannel):
        return
        
    infochannel = client.get_channel(744934787118268488)    #Cambiar el ID de este canal por el ID del canal donde quieras que llegue la info de los examenes.
    
    aprobado = discord.utils.get(ctx.guild.roles, name="aprovado")#Cambiar name="ROL DE APROBADO" por el nombre del rol que quieras dar si el usuario aprueba.
    desaprobado = discord.utils.get(ctx.guild.roles, name="desaprovado")#Igualmente cambiar por el respectivo nombre del rol en tu servidor.
    
    
    puntos = 0
    timerstart = time.monotonic()
    for pregunta in preguntas:
        await ctx.message.author.send(pregunta.preg)

        def check(m):
            return m.channel == ctx.author.dm_channel and m.author == ctx.author
        respuesta = pregunta.resp
        msg = await client.wait_for("message", check=check)
        if msg.content.lower() == respuesta:
            puntos += 1
    timerend =round((time.monotonic() - timerstart), 1)
    
    #En este condicional se determina cuantas preguntas acertadas se necesitan para aprobar. Por ejemplo, igual o mas de 3.
    if puntos >= 3:
        await ctx.author.add_roles(aprobado)
        await ctx.author.remove_roles(desaprobado)
    else:
        await ctx.author.add_roles(desaprobado)
        await ctx.author.remove_roles(aprobado)
    
    #El mensaje que se envia al canal de informacion despues del test.
    await infochannel.send("El usuario " + str(ctx.message.author) + " completo el examen en " + str(timerend) + " segundos.\nRespuestas acertadas: " + str(puntos) + "/" + str(len(preguntas)))
    
client.run('TOKEN') #Poner el Token ID de tu bot en este espacio.