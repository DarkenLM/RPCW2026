# TPC3
**Titulo:** Semana 4  
**Id:** PG60298  
**Nome:** Rafael Santos Fernandes  
**Data:** 2026-03-06  
<img src="../assets/img/foto.jpg" alt="foto" width="200" />

## Resumo
Este trabalho incidiu sobre a construção, povoação e exploração da ontologia 'Biblioteca Temporal'.

## Resultados
## 1. Construção da Ontologia
### 1.1. Metodologia 
Foram criadas as classes conforme descritas no enunciado, pela hierarquia definida no mesmo. Por consequência desta abordagem, a classe `Pessoa` e suas subclasses estão representadas tanto como descendente direto de `owl:Thing` como de `Agente`.  
Foram também criados os indivíduos conforme descritos no enunciado, bem como os indivíduos `Big_Bang`, `Formação_da_Via_Láctea`, `Morte_Térmica_do_Universo` e `Gênesis` para testar as restrições aplicadas ás classes e propriedades de objetos.  
As propriedades de objeto foram nomeadas conforme extraído dos datasets através da ferramenta `getProps`.  

### 1.2. Limitações 
Para a construção da ontologia, foi exigido uma restrição em OWL: `Um Autor não pode ser Leitor do mesmo livro na mesma linha temporal.`.  
Esta restrição pode ser representada através da fórmula em Lógica de Primeira Ordem $$\forall_{a} . Autor(a) \wedge Leitor(a) \Rightarrow \nexists_{l,t} . Livro(l) \wedge LinhaTemporal(t) \wedge escritoPor(l,a) \wedge requisitam(a,l) \wedge existeEm(l,t) \wedge autorouEm(a,t)$$.  
Esta é uma relação ternária que é, porém, impossível de resolver em Lógica Descritiva, dado existirem co-referências entre as variáveis em dois ramos diferentes da fórmula nos últimos dois predicados da mesma, que são avaliados separadamente (i.e. $existeEm(l,t) \wedge autorouEm(a,t)$ é interpretado como *$l$ existeEm* ***qualquer uma*** *linha temporal $t_1$, e $a$ autorouEm* ***qualquer uma*** *linha temporal $t_2$*, o que não garante que $t_1$ e $t_2$ representem a mesma linha temporal.)  
Para representar esta fórmula seria necessário o uso de um sistema que permita o uso de Cláusulas de Horn, como SWRL ou SHACL.  

### 1.3. Resultado 
Contém a estrutura base da ontologia, sem nenhum dado da população, que será utilizado pela fase seguinte para gerar o ficheiro TTL final contendo a intologia finalizada.  
> **Ficheiro relacionado:** [./ontologias/biblioteca_temporal_base.ttl](./ontologias/biblioteca_temporal_base.ttl)

## 2. Scripts de Utilitário
### 2.1. getProps.py 
Criado para extraír metainformação de um dado ficheiro de população, dado que as chaves das propriedades de objeto presentes nos ficheiros de população fornecidos diferem das chaves mencionadas no enunciado. Dada a diferença, foi criada a ferramenta para rápida e fácilmente adaptar a ontologia base para aceitar os indivíduos dos mesmos.  
Esta ferramenta extraí as seguintes metainformações:  
- Quais as classes utilizadas pelos indivíduos.  
- Quais as propriedades de objeto utilizadas pelos indivíduos.  
- Quais os possíveis valores para uma dada propriedade de objeto de entre todos os indivíduos que a declarem.  
> **Ficheiro relacionado:** [./scripts/getProps.py](./scripts/getProps.py)
### 2.2. populate.py 
Criado para extraír e adicionar indivíduos a uma dada ontologia base a partir de um dado ficheiro de população, em JSON.  
Esta ferramenta utiliza a biblioteca rdflib para ler, processar e gravar as ontologias, tanto em XML ou TTL (configurável).  
> **Ficheiro relacionado:** [./scripts/populate.py](./scripts/populate.py)
### 2.3. populate.sh 
- **Descrição:** Script de bash para popular automaticamente a ontologia base com o ficheiro de população `dataset_temporal_v2_100.json`  
- **Ficheiro relacionado:** [./populate.sh](./populate.sh)

## 3. Queries SPARQL
### 3.1.  Liste todos os livros que existem na linha temporal original (LinhaOriginal). 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT * WHERE {  
    ?linha a :LinhaOriginal .  
    ?livro a :Livro ;  
       :existeEm ?linha .  
     
}  
```  

### 3.2.  Identifique os livros que existem em mais do que uma linha temporal. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro (COUNT(?linha) AS ?numLinhas) WHERE {  
    ?linha a :LinhaTemporal .  
    ?livro a :Livro ;  
       :existeEm ?linha .  
     
}  
GROUP BY ?livro  
HAVING (?numLinhas > 1)  
ORDER BY DESC(?numLinhas)  
```  

### 3.3.  Liste todos os livros classificados como LivroParadoxal. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro WHERE {  
    ?livro a :LivroParadoxal ;  
}  
```  

### 3.4.  Para cada LivroHistorico, indique os eventos históricos que esse livro refere. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro ?evento WHERE {  
    ?livro a :LivroHistorico ;  
           :refereEvento ?evento .  
}  
```  

### 3.5.  Identifique livros classificados como LivroHistorico que referem eventos futuros. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro ?evento WHERE {  
    ?livro a :LivroHistorico ;  
           :refereEvento ?evento .  
    ?evento a :EventoFuturo  
}  
```  

### 3.6.  Liste os autores e o número de livros que escreveram, ordenando o resultado por número de livros em ordem decrescente. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?autor ?nomeAutor (COUNT(?livro) AS ?numLivros) WHERE {  
    ?livro :escritoPor ?autor .  
    OPTIONAL { ?autor :nome ?nomeAutor }  
}  
GROUP BY ?autor ?nomeAutor  
ORDER BY DESC(?numLivros)   
```  

### 3.7.  Identifique os autores que escreveram pelo menos um livro paradoxal. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?autor ?nomeAutor WHERE {  
    ?_livro :escritoPor ?autor .  
    ?_livro a :LivroParadoxal .  
    OPTIONAL { ?autor :nome ?nomeAutor . }  
}  
```  

### 3.8.  Liste todos os livros que existem em pelo menos uma linha temporal alternativa (LinhaAlternativa). 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT DISTINCT ?livro WHERE {  
    ?_linha a :LinhaAlternativa .  
    ?livro a :Livro ;  
           :existeEm ?_linha .  
}  
```  

### 3.9.  Indique todos os bibliotecários e a biblioteca onde trabalham. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?bibliotecário ?biblioteca WHERE {  
    ?bibliotecário :trabalhaEm ?biblioteca .  
}  
```  

### 3.10.  Liste todos os livros escritos por Cronos e indique em que linhas temporais esses livros existem. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro ?linha WHERE {  
    ?livro :escritoPor :Cronos ;  
           :existeEm ?linha  
}  
ORDER BY ?livro  
```  

### 3.11.  Identifique livros que não referem nenhum evento. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro (COUNT(?evento) AS ?numEventos) WHERE {  
    ?livro a :Livro .  
    OPTIONAL { ?livro :refereEvento ?evento . }  
}  
GROUP BY ?livro  
HAVING (?numEventos = 0)  
ORDER BY ?livro  
```  

### 3.12.  Verifique se existe algum livro sem linha temporal associada. 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?livro (COUNT(?linha) AS ?numLinhas) WHERE {  
    ?livro a :Livro .  
    OPTIONAL { ?livro :existeEm ?linha . }  
}  
GROUP BY ?livro  
HAVING (?numLinhas = 0)  
ORDER BY ?livro  
```  

### 3.13.  Identifique autores que sejam também leitores (caso essa propriedade esteja modelada). 
```sparql  
PREFIX : <http://rpcw.di.uminho.pt/biblioteca_temporal/>  
SELECT ?pessoa  
WHERE {  
    ?pessoa a :Autor .  
    ?pessoa a :Leitor .  
}  
```  



