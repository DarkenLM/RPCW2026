# TPC6
**Titulo:** Semana 6  
**Id:** PG60298  
**Nome:** Rafael Santos Fernandes  
**Data:** 2026-03-21  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
Este trabalho incidiu sobre a extensão da aplicação web desenvolvida no TPC5 para adicionar um meio de consulta da informação relativa a linhas temporais.

## Resultados
## 1. Aplicação Web
### 1.1. Estrutura 
A estrutura da aplicação web mantém-se inalterada, salvo a adição do template da página `linha`:  
```  
web  
├── app  
│   ├── pages  
│   │   ├── app  
│   │   │   ├── linha.html.j2  
```  

### 1.2. Alterações 
- Foi adicionada uma nova rota `/linha/<linha>` que obtém a informação relativa a uma linha temporal com o id `:<linha>`. A página apresenta uma lista com o id, título e tipos para todos os livros que existem nessa mesma linha temporal.  
- Foram organizados os macros utilizados nos templates, tendo sido movidos para o template `base` macros com uso nos templates `iterator` e `entry`, para evitar repetição de código e manter consistência visual na interface.  

### 1.3. Resultado 
Contém toda a nova versão aplicação web.  
> **Ficheiro relacionado:** [./web](./web)

## 2. Scripts de Utilitário
### 2.1. makeenv.py 
Criado para fácilmente criar e ativar um *Virtual Environment* python para isolar as bibliotecas utilizadas pelo projeto.  
> **Ficheiro relacionado:** [./web/makeenv.py](./web/makeenv.py)
### 2.2. run.py 
Criado para fácilmente iniciar a aplicação web. Carrega automaticamente as variáveis de ambiente a partir do ficheiro `.env` localizado no mesmo diretório que o script, ou localizado no diretório de trabalho atual, caso o anterior esteja em falta.  
> **Ficheiro relacionado:** [./web/run.py](./web/run.py)


