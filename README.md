# 🎯 FocusTrack

> **Estude com intenção.**

O **FocusTrack** é um aplicativo desktop de produtividade desenvolvido em **Python + Flet**, criado para ajudar estudantes a organizar suas sessões de estudo, controlar o tempo de foco e acompanhar o histórico de estudos.

O projeto foi desenvolvido como atividade prática para aplicar os conceitos aprendidos sobre a biblioteca **Flet**, incluindo criação de interfaces, layouts, formulários, gerenciamento de estado, listas dinâmicas e atualização da interface.

---

## 💡 Sobre o projeto

Durante os estudos, é comum perder o controle sobre quanto tempo foi dedicado a cada matéria ou assunto.

Pensando nisso, o FocusTrack foi desenvolvido como uma ferramenta simples para:

* ⏱️ Controlar sessões de estudo através de um cronômetro;
* 📚 Registrar matérias e assuntos estudados;
* 📊 Acompanhar o tempo total de estudo;
* 🔎 Pesquisar sessões já registradas;
* 🗂️ Filtrar sessões por matéria e período;
* ✏️ Editar registros;
* 🗑️ Excluir sessões;
* 💾 Armazenar os dados de forma persistente utilizando SQLite.

A proposta é transformar pequenos períodos de concentração em um histórico de evolução.

---

## 🚀 Funcionalidades

### 📊 Dashboard

A tela inicial apresenta um resumo dos estudos realizados:

* Tempo estudado no dia;
* Quantidade total de sessões;
* Tempo total acumulado;
* Tempo estudado por matéria;
* Sessões mais recentes;
* Data atual.

---

### ⏱️ Cronômetro de foco

O aplicativo possui um cronômetro inspirado na técnica **Pomodoro**.

É possível:

* Definir a duração da sessão;
* Iniciar o cronômetro;
* Pausar a sessão;
* Continuar uma sessão pausada;
* Reiniciar o cronômetro;
* Acompanhar visualmente o progresso;
* Receber uma mensagem quando a sessão termina.

O tempo padrão é de **25 minutos**, mas pode ser alterado pelo usuário.

---

### 📝 Registro de sessões

O usuário pode registrar uma sessão informando:

* **Matéria**
* **Assunto**
* **Duração**
* **Data**

Exemplo:

```text
Matéria: Matemática
Assunto: Funções
Duração: 50
Data: 2026-09-11
```

Os registros são armazenados no banco de dados e permanecem disponíveis mesmo depois que o aplicativo é fechado.

---

### 🔎 Busca e filtros

A tela de sessões permite encontrar registros rapidamente através de:

* Busca por matéria;
* Busca por assunto;
* Filtro por matéria;
* Filtro por período.

Os períodos disponíveis são:

* Todos;
* Hoje;
* Últimos 7 dias;
* Últimos 30 dias.

---

### ✏️ Edição e exclusão

Cada sessão registrada pode ser:

* Editada;
* Excluída.

Ao editar uma sessão, os dados existentes são carregados automaticamente no formulário para que possam ser alterados.

---

## 🛠️ Tecnologias utilizadas

### Python

Linguagem principal utilizada no desenvolvimento da aplicação.

### Flet

Biblioteca utilizada para construir a interface gráfica do aplicativo utilizando Python.

Foram utilizados conceitos como:

* `Row`
* `Column`
* `Container`
* `Text`
* `TextField`
* `Dropdown`
* `ElevatedButton`
* `TextButton`
* `ProgressBar`
* Gerenciamento de eventos
* Atualização da interface com `page.update()`

### SQLite

Banco de dados utilizado para armazenar as sessões de estudo.

A aplicação cria automaticamente o arquivo:

```text
focustrack.db
```

### Asyncio

Utilizado para controlar o funcionamento assíncrono do cronômetro sem travar a interface.

---

## 🗃️ Estrutura do banco de dados

O FocusTrack utiliza uma tabela chamada `sessions`.

| Campo       | Tipo    | Descrição                 |
| ----------- | ------- | ------------------------- |
| `id`        | INTEGER | Identificador da sessão   |
| `materia`   | TEXT    | Matéria estudada          |
| `assunto`   | TEXT    | Assunto estudado          |
| `duracao`   | INTEGER | Duração em minutos        |
| `data`      | TEXT    | Data da sessão            |
| `criado_em` | TEXT    | Data e horário de criação |

O banco é criado automaticamente na primeira execução do programa.

---

## 🎨 Interface

O design do FocusTrack foi desenvolvido de forma autoral, utilizando uma identidade visual baseada em tons:

* Verde escuro;
* Bege;
* Branco;
* Terracota.

A interface foi pensada para ser **limpa, minimalista e focada em produtividade**, evitando excesso de elementos visuais.

### Principais telas

#### Dashboard

Tela principal com estatísticas, cronômetro, matérias e sessões recentes.

![Dashboard](screenshots/dashboard.png)

#### Sessões

Tela responsável pela visualização, pesquisa e filtragem dos estudos registrados.

![Sessões](screenshots/sessoes.png)

#### Nova sessão

Formulário utilizado para registrar ou editar uma sessão de estudo.

![Nova sessão](screenshots/nova-sessao.png)

---

## 📂 Estrutura do projeto

```text
FocusTrack/
│
├── main.py
├── focustrack.db
├── README.md
│
└── screenshots/
    ├── dashboard.png
    ├── sessoes.png
    └── nova-sessao.png
```

> O arquivo `focustrack.db` é criado automaticamente pelo programa e pode ser gerado novamente caso não exista.

---

## ▶️ Como executar

### 1. Clone o repositório

```bash
git clone https://github.com/SEU-USUARIO/FocusTrack.git
```

### 2. Entre na pasta

```bash
cd FocusTrack
```

### 3. Instale o Flet

```bash
pip install flet
```

### 4. Execute o programa

```bash
python main.py
```

O aplicativo será iniciado em uma janela própria.

---

## 📋 Validação dos dados

O sistema possui validações para evitar registros inválidos.

Por exemplo:

* A matéria não pode ficar vazia;
* O assunto não pode ficar vazio;
* A duração precisa ser um número positivo;
* A data deve seguir o formato `AAAA-MM-DD`.

Caso algum dado esteja incorreto, o usuário recebe uma mensagem de aviso.

---

## 🧠 Conceitos aplicados

Este projeto foi desenvolvido utilizando diversos conceitos estudados durante as aulas:

* Estruturação de interfaces com Flet;
* Containers;
* Linhas e colunas;
* Componentes reutilizáveis;
* Eventos de clique;
* Formulários;
* Campos de entrada;
* Listas dinâmicas;
* Filtros;
* Gerenciamento de estado;
* Atualização da interface;
* Programação assíncrona;
* Manipulação de banco de dados;
* CRUD;
* Validação de dados;
* Organização de código em funções e classes.

---

## 🔄 Operações CRUD

O projeto também implementa as quatro operações básicas de manipulação de dados:

| Operação | Implementação                  |
| -------- | ------------------------------ |
| Create   | Criar uma nova sessão          |
| Read     | Visualizar sessões registradas |
| Update   | Editar uma sessão              |
| Delete   | Excluir uma sessão             |

---

## 🎯 Objetivo da atividade

O objetivo deste projeto foi desenvolver uma aplicação **autoral e funcional**, colocando em prática os conhecimentos adquiridos sobre a biblioteca Flet e desenvolvimento de interfaces gráficas em Python.

Além de cumprir os requisitos técnicos da atividade, o FocusTrack busca resolver um problema real: **ajudar estudantes a manter consistência e organização durante os estudos.**

---

## 👨‍💻 Autor

**Pedro de Oliveira**

Projeto desenvolvido como atividade acadêmica utilizando **Python + Flet + SQLite**.

---

## 📌 Status

🟢 **Concluído**

O projeto possui interface funcional, persistência de dados, cronômetro, cadastro, edição, exclusão, busca e filtros de sessões.

---

> **FOCUS / TRACK**
> *Disciplina > Motivação*
> *Pequenos blocos de foco, consistentemente.*
