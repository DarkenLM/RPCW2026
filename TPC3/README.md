# TPC3
**Titulo:** Semana 3  
**Id:** PG60298  
**Nome:** Rafael Santos Fernandes  
**Data:** 2026-02-26  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
Este trabalho incidiu sobre a tecnologia de base de dados GraphDB e a linguagem SPARQL.

## Resultados
## 1. Manifesto
### 1.1. Gerador de Manifestos 
Nova versão do gerador de manifestos para suportar resulados que não envolvam ficheiros.  
- Propriedade `file` é agora opcional.  
- Adicionada propriedade `name` ao objeto de resultado, que define um nome opcional para o resultado.  
- Reestruturado o formato de resultados no markdown resultante.  
- Adicionado suporte a múltiplas linhas de texto para a propriedade `desc` através do uso de um array em vez de uma string. Valores em string ainda suportados.  
> **Ficheiro relacionado:** [./manifest/makeManifest.py](./manifest/makeManifest.py)

## 2. Polvo Filosófico
### 2.1. Alterações á Topologia 
- Movida classe `PratoComPolvo` de `owl:Thing` para `PratoCarnívoro`.  
- Removido indivíduo `PolvoIngrediente`.  
- Substituída propriedade `:temIngrediente PolvoIngrediente` por `:temIngrediente IngredientePolvo` no indivíduo `EnsopadoCanibal`.  


## 3. Queries SPARQL
### 3.1. Quem foram os clientes? 
#### Query  
```sparql  
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
PREFIX owl: <http://www.w3.org/2002/07/owl#>  
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  
PREFIX : <http://example.org/polvo-filosofico#>  
SELECT * WHERE {  
    ?s a :Cliente .  
}  
```  
  
#### Resposta (CSV)  
```  
s  
:Ana  
:Bruno  
:Carla  
:Daniel  
:Eva  
:Schrodinger  
```  

### 3.2. Que pratos serve o restaurante? 
#### Query  
```sparql  
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
PREFIX owl: <http://www.w3.org/2002/07/owl#>  
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  
PREFIX : <http://example.org/polvo-filosofico#>  
SELECT * WHERE {  
    ?s a :Prato .  
}  
```  
  
#### Resposta (CSV)  
```  
s  
:SaladaExistencial  
:EnsopadoCanibal  
:PratoDoDia  
:BifeDeterminista  
:PratoDoObservador  
:DilemaDoSer  
:PeixeDoLivreArbitrio  
:TofuMetafisico  
```  

### 3.3. Quais os ingredientes necessários á confecção dos pratos (todos)? 
#### Query  
```sparql  
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
PREFIX owl: <http://www.w3.org/2002/07/owl#>  
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  
PREFIX : <http://example.org/polvo-filosofico#>  
SELECT DISTINCT ?i WHERE {  
    ?s a :Prato ;  
       :temIngrediente ?i  
}  
```  
  
#### Resposta (CSV)  
```  
i  
:Alface  
:Tomate  
:PolvoIngrediente  
:IngredientePolvo  
:CarneVaca  
:Cogumelos  
:Peixe  
:Tofu  
```  

### 3.4. Há funcionários que sejam também clientes? 
#### Query  
```sparql  
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>  
PREFIX owl: <http://www.w3.org/2002/07/owl#>  
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>  
PREFIX : <http://example.org/polvo-filosofico#>  
SELECT * WHERE {  
    ?s a :Funcionario ,  
         :Cliente  
}  
```  
  
#### Resposta (CSV)  
```  
s  
:Schrodinger  
```  



