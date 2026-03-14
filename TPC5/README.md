# TPC5
**Titulo:** Semana 5  
**Id:** PG60298  
**Nome:** Rafael Santos Fernandes  
**Data:** 2026-03-14  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
Este trabalho incidiu sobre a construção de uma aplicação web com vista a consultar a informação de uma ontologia carregada em GraphDB.

## Resultados
## 1. Aplicação Web
### 1.1. Estrutura 
A aplicação web foi criada utilizando a biblioteca `Flask`, com recurso á funcionalidade de `Blueprints` e templates `Jinja2` expostos pela mesma.  
A estrutura dos ficheiros é a seguinte:  
```  
web  
├── app  
│   ├── pages  
│   │   ├── app  
│   │   ├── templates  
│   │   ├── 404.html.j2  
│   │   └── base.html.j2  
│   ├── public  
│   │   ├── css  
│   │   └── js  
│   ├── routes  
│   ├── services  
│   │   └── sparqlService.py  
│   ├── __init__.py  
│   ├── logger.py  
│   ├── types.py  
│   └── util.py  
├── main.py  
```  
Onde:  
- O diretório `web/app/pages/app` contém os templates das páginas definidas pelas rotas.  
- O diretório `web/app/pages/templates` contém templates reutilizáveis.  
- O template `web/app/pages/404.html.j2` contém o template para a página do erro HTML 404.  
- O template `web/app/pages/base.html.j2` contém o layout para todas as páginas  
- O diretório `web/app/public` contém ficheiros estáticos, separados por subdiretórios através seu tipo.  
- O diretório `web/app/routes` contém os routers, definidos através de `Blueprints` do Flask, que definem as rotas da aplicação.  
- O diretório `web/app/services` contém conjuntos de funções que expõem funcionalidades ás rotas.  
- O serviço `web/app/services/sparqlService.py` contém a funcionalidade de interação com um endpoint SPARQL.  
- O módulo `web/app/__init__.py` define a aplicação Flask.  
- O módulo `web/app/logger.py` contém um logger que pode ser reutilizado e instanciado por toda a aplicação.  
- O módulo `web/app/types.py` contém ***tipos*** utilitários.  
- O módulo `web/app/util.py` contém utilitários relativos á localização e renderização de rotas, bem como outras funcionalidades sem classificação.  
- O módulo `web/main.py` define a CLI da aplicação, e instancia a mesma.  

### 1.2. Variáveis de Ambiente 
A aplicação utiliza as seguintes variáveis de ambiente:  
- `GRAPHDB_ENDPOINT`: URL que aponta para um endpoint SPARQL.  
- `RDF_PREFIX`: O prefixo (`:`) utilizado para os indivíduos, predicados e propriedades da ontologia.  

### 1.3. Resultado 
Contém toda a aplicação web desenvolvida.  
> **Ficheiro relacionado:** [./web](./web)
### 1.4. Ontologia Alvo 
Contém a ontologia com os dados para a aplicação.  
> **Ficheiro relacionado:** [./bib_temp.ttl](./bib_temp.ttl)

## 2. Scripts de Utilitário
### 2.1. makeenv.py 
Criado para fácilmente criar e ativar um *Virtual Environment* python para isolar as bibliotecas utilizadas pelo projeto.  
> **Ficheiro relacionado:** [./web/makeenv.py](./web/makeenv.py)
### 2.2. run.py 
Criado para fácilmente iniciar a aplicação web. Carrega automaticamente as variáveis de ambiente a partir do ficheiro `.env` localizado no mesmo diretório que o script, ou localizado no diretório de trabalho atual, caso o anterior esteja em falta.  
> **Ficheiro relacionado:** [./web/run.py](./web/run.py)


