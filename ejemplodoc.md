

INFORME DE ACTIVIDAD DESARROLLADA
Nombre completo


Escribe tu nombre y apellidos 
Asignatura
Desarrollo de Sistemas 2
Unidad o Tema
Unidad 1: Especificación de requisitos de Sistemas
Actividad/Recurso
Actividad 3.1


DESCRIPCIÓN DE LA ACTIVIDAD
Título de la actividad: “Especificación de requisitos" 

Pegar aquí 













Especificación de Requisitos de Software


















Kevin Gustavo Zarate Espinoza
UNIVERSIDAD PRIVADA DOMINGO SAVIO

COVID-19 SOFTWARE










Integrantes



Kevin Gustavo Zarate Espinoza



























Proyecto de software resultado de la investigación “Registro del avance de Covid 19.
Infectados, recuperados, decesos”,





















Universidad Privada Domingo Savio




Contenido
Introducción	4
Propósito	4
Ámbito del Sistema	4
Definiciones, Acrónimos y Abreviaturas	5
Referencias	7
Visión General del Documento	7
Análisis de requerimientos de software	7
Descripción General	7
Perspectiva del Producto	7
Funciones del Producto	8
Características de los usuarios	9
Restricciones	9
Suposiciones y Dependencias.	10
Requerimientos Específicos	10
Requerimientos Funcionales.	10
Requerimientos No Funcionales	14
Diseño de software	15
Descripción del Sistema	15
Arquitectura del Sistema	16
Diseño de Datos	17
Descripción de Datos	17
Diccionario de Datos	18
Diseño del Componente	23
Listado de Componentes	23
Diseño de Interface	26
Visión General de la Interfaz de Usuario	26
Imágenes de la Interfaz	28
Matriz de Requerimientos	37
Implementación del Software	38
Descripción General	38

Código fuente	38
Pruebas de errores en el código	38
Pruebas en el Front-end	38
Pruebas en el Back-end	38
Validación	39
Descripción General	39
Casos de validación	39

Nombre del Software: Covid 19 Software

Autores: Kevin Gustavo Zarate Espinoza


Centro de Costo del Proyecto: Covid 19

Introducción

Este documento es la Especificación de Requisitos Software para mantener al tanto de los datos de contagios, decesos y recuperados de covid 19 basándose en las pruebas de PCR


Propósito

Dar a conocer en que situación nos encontramos ante el nuevo virus del covid 19, a nivel de toda Bolivia.

Ámbito del Sistema

Con este proyecto Covid 19 se busca desarrollar e implementar un aplicativo web para todo acceso publico y privado. Para fomentar el cuidado y la prevención ante el contagio.


Gracias al desarrollo de Covid 19 se espera:

Identificar las falencias y  fortalezas  que  podemos  tener  si contraemos el covid 19.
Agilizar el proceso de recolección de información a través de las encuestas digitales enfocadas en los puntos de interés de cada persona.
Brindar diagnósticos precisos basados en los criterios de evaluación establecidos en el proyecto de investigación.
Servir de plataforma guía para promover 
Los cuidados y prevención que debemos tener ente esta nueva amenaza.


Definiciones, Acrónimos y Abreviaturas


Covid 19: Coronavirus 2019.


UPDS: Universidad Privada Domingo Savio.

RF: Requerimiento Funcional

RNF: Requerimiento No Funcional

Look and Feel: Aspecto visual del Sistema.

Front-end: Es todo lo que se puede observar del lado del cliente, es decir, el apartado visual de la aplicación. Por lo general se ocupan tecnologías como: HTML5, CSS3, JavaScript entre otros para la construcción de las interfaces. En este proyecto se utiliza HTML5 como herramienta de desarrollo para el Front-end.

Back-end: El trabajo del desarrollador en la parte de back-end es todo lo que va anclado al servidor de la aplicación, al core del negocio, sin este la aplicación desarrollada en el front-end no tendría una funcionalidad.


Windows Forms en Visual Studio con C #: En esta breve introducción al entorno de desarrollo integrado (IDE) de Visual Studio, creará una aplicación sencilla de C- que tiene una interfaz de usuario (UI) basada en Windows.
Referencias

Standard IEEE 830 – 1998, IEEE.
Visión General del Documento

El contenido principal de este documento se constituye con la descripción del software a construir y sus requerimientos, así como el diseño de cada una de sus facetas, tales como, arquitectura, datos, interfaces, etc.

Finalmente, el detalle de la implementación, lo cual comprende el código fuente, pruebas y manejo de errores y escenarios.

Análisis de requerimientos de software


Descripción General

Se tiene estimado que Covid 19 sea una aplicación para estimar los conteos de los resultados y dar el conocimiento a las personas de toda Bolivia.

Perspectiva del Producto

Covid 19 esta planteado como un software independiente cuyo funcionamiento esta ligado a mantener los resultados de las pruebas de PCR.

Funciones del Producto



 

Características de los usuarios

Tipo de Usuario
Administrador
Nivel Educacional
Educación Superior / Investigador Proyecto COVID 19
Experiencia
Gestión de Sistemas de información.
Actividades
Configurar y ajustar los parámetros de funcionamiento del software.
Administración de Usuarios.


Tipo de Usuario
Moderador
Nivel Educacional
Cursar programa de Educación Superior / Auxiliar de
Investigación.
Experiencia
Manejo básico de Sistemas de Información
Actividades
Revisión estatus de proyecto.




Restricciones

El uso del software requiere de conexión a internet.
Interfaces de usuario Intuitivas.
Funcional en los navegadores más comunes.
Debe ser construida como una aplicación cliente-servidor.
La comunicación entre cliente y servidor deberá establecerse a través de protocolos HTTP.
El aplicativo debe contar con un sistema de validación de sesión.
Todo usuario Moderador debe tener noción de los diferentes criterios de evaluación indicados en el Proyecto de Investigación para realizar la calificación de las encuestas.

Suposiciones y Dependencias.

Los equipos en donde sea desplegada la aplicación deben contar con un mínimo de recursos para el correcto funcionamiento.
Requerimientos Específicos

Requerimientos Funcionales.



Código del Requerimiento
RF02
Nombre
Autentificación
Propósito
Iniciar sesión en el aplicativo web COVID 19.
Descripción
Una vez ubicados  la aplicaciom de inicio de sesión, el usuario debe diligenciar sus credenciales en los
respectivos campos y finalizar pulsando el botón de inicio de sesión.
Entrada
Credenciales.
Salida
Redirección a la página principal del usuario.
Prioridad
Alta
Código del Requerimiento
RF05
Nombre
Creación de Moderador
Propósito
Crear nuevo usuario del sistema con privilegios de moderador que pueda realizar las revisiones.
Descripción
Dentro del componente de usuarios, únicamente accesible para los administradores, el botón de “Agregar” desplegará un formulario donde se
diligenciará la información del nuevo moderador.
Entrada
Formulario de creación de Moderador.
Salida
Mensaje	al	correo	del	moderador	con	sus credenciales.
Prioridad
Media




Código del Requerimiento
RF08
Nombre
Modificar covid 19
Propósito
Corregir o actualizar información de cualquier tipo de usuario.
Descripción
A través del componente de perfil, cada usuario del sistema tiene la facilidad de modificar su información.
Entrada
Formulario de Perfil.
Salida
Mensaje de acción satisfactoria.
Prioridad
Media





Requerimientos No Funcionales

Código del Requerimiento
RNF01
Nombre
Look and Feel
Descripción
El aspecto del aplicativo debe ser consistente en todas sus páginas, además de amigable e intuitivo hacia el usuario.
Prioridad
Alta



Código del Requerimiento
RNF02
Nombre
Seguridad
Descripción
El protocolo o librería usado para manejar la seguridad en la sesión del usuario debe ser lo suficientemente confiable.
La información sensible, como contraseñas debe manipular bajo algún nivel de encriptación o cifrado.
Prioridad
Alta



Código del Requerimiento
RNF03
Nombre
Restricción de Contenido
Descripción
El acceso a cada página del aplicativo está determinado por el rol del usuario.
Prioridad
Alta



Código del Requerimiento
RNF04
Nombre
Confidencialidad
Descripción
Toda la información otorgada por los usuarios se manipulará únicamente con fines corporativos y de
manera limpia.
Prioridad
Alta



Código del Requerimiento
RNF05
Nombre
Robustez
Descripción
El software debe ser capaz de manejar toda la información recolectada a través del tiempo con
fluidez.
Prioridad
Media



Diseño de software

Descripción del Sistema

COVID 19 se plantea como un software construido bajo los estándares de desarrollo Windows Forms actuales, tomando como punto partida, la implementación de su base de datos de datos sobre un motor gratuito, tal como SqlServer.


Gracias a la conjunción de estas tecnologías (y algunas otras inherentes a ellas) es posible construir una aplicación confiable, moderna y de gran rendimiento, ya que estas interactúan con sinergia y son de moderado entendimiento, lo cual permite a los desarrolladores ascender en la curva de aprendizaje con mayor facilidad.



Diseño de Datos

Descripción de Datos

El flujo de la información en el aplicativo está sujeto al proceso y a la capa en donde se esté procesando la misma. Mientras en el Front-end la información es encapsulada en clases e interfaces que representan las entidades, en el Back- end se separan en entidades de base de datos para los repositorios y en modelos o DTO (Data Transfer Object) para los controladores y servicios.

Modelo Entidad Relación


Diccionario de Datos

COVID 19

SELECT 
FROM     dbo.DECESO INNER JOIN
                  dbo.PACIENTE ON dbo.DECESO.COD_DECES = dbo.PACIENTE.COD_PACIEN INNER JOIN
                  dbo.INFECTADO ON dbo.PACIENTE.COD_PACIEN = dbo.INFECTADO.COD_INFEC INNER JOIN
                  dbo.MUNICIPIO ON dbo.PACIENTE.COD_MUNIC = dbo.MUNICIPIO.COD_MUNIC INNER JOIN
                  dbo.PROVINCIA ON dbo.MUNICIPIO.COD_PROVI = dbo.PROVINCIA.COD_PROVI INNER JOIN
                  dbo.DEPARTAMENTO ON dbo.PROVINCIA.COD_DEPTO = dbo.DEPARTAMENTO.COD_DEPTO INNER JOIN
                  dbo.RECUPERADO ON dbo.PACIENTE.COD_PACIEN = dbo.RECUPERADO.COD_RECUP




Diseño de Interface


Visión General de la Interfaz de Usuario

A cada usuario del sistema se le presentará una serie de interfaces acorde al rol que posea.


Interfaces compartidas

Inicio de Sesión: Permite a todo usuario, ingresar al sistema a través de las credenciales registradas o asignadas en el caso del moderador.
Perfil: Permite a todo usuario revisar y actualizar su información personal.



Imágenes de la Interfaz

Interfaz de Registro (Rol Usuario)



Interfaz de Inicio de Departamento




Interfaz de controles 


Implementación del Software

Descripción General

Para llevar a cabo la implementación del software, plasmando en componentes los requerimientos levantados, es necesario que los desarrolladores mantengan abierto un canal de comunicación constante con su líder de investigación.

Cada componente debe estar sometido a la evaluación del investigador y a una serie de casos de prueba, pruebas de integración, así como la documentación en los diferentes niveles o capas, los cuales son Datos, Servicios y Aplicación.

Finalmente, toda la configuración inicial del software, necesaria para su correcto funcionamiento debe estar disponible a través de los respectivos casos de covid 19.


Código fuente

El código fuente fue anexado en la carpeta junto a este documento.

Pruebas de errores en el código

Los casos de prueba deben comprender los diversos escenarios en donde un usuario puede ocasionar un posible error, pues toda excepción dentro del código debe manejarse y mostrarse de manera amigable al usuario.


Pruebas en el Front-end

Violar las validaciones.
Cancelar la carga de la página durante procesos cruciales.
Exigir la carga de la página con altas cantidades de controles dinámicos.
Alterar peticiones http (modificar URL).

Pruebas en el Back-end

Reiterar llamadas a servicios.
Enviar parámetros vacíos o fuera del rango.
Enviar atributos nulos no permitidos (nativos).

Validación

Descripción General

Para la validación de “COVID 19” se conto en la evaluación del docente asigna en la materia Desarrollo de Sistemas I.

