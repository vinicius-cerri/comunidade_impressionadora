from flask import render_template, flash, redirect, url_for, request, abort
from comunidadepython import app, database, bcrypt
from comunidadepython.forms import FormLogin, FormCriarConta, FormEditarPerfil, FormCriarPost
from comunidadepython.models import Usuario, Post
from flask_login import login_user, logout_user, current_user, login_required
from PIL import Image
import secrets
import os


# Página Inicial
@app.route('/')
def homepage():
    posts = Post.query.order_by(Post.id.desc())
    return render_template('homepage.html', posts=posts)


# Página de Contato
@app.route('/contato')
def contato():
    return render_template('contato.html')


# Página de Usuários
@app.route('/usuarios')
@login_required
def usuarios():
    lista_usuarios = Usuario.query.all()
    return render_template('usuarios.html', lista_usuarios = lista_usuarios)


# Página de Login/Criar Conta
@app.route('/login', methods=['GET', 'POST'])
def login():
    form_login = FormLogin()
    form_criarconta = FormCriarConta()

    # Fez o Login com Sucesso
    if form_login.validate_on_submit() and 'botao_submit_login' in request.form:
        # Verificar se o Usuário existe
        usuario = Usuario.query.filter_by(email=form_login.email.data).first()
        if usuario and bcrypt.check_password_hash(usuario.senha, form_login.senha.data):
            # Fazer Login
            login_user(usuario, remember = FormLogin.lembrar_dados)
            # Exibir mensagem de Login bem Sucedido
            flash(f'Login feito com sucesso no e-mail: {form_login.email.data}', 'alert-success')
            # Redirecionamento Inteligente
            parametro_next = request.args.get('next')
            if parametro_next:
                # Redicionar para a Página que o usuário estava tentando acessar
                return redirect(parametro_next)
            else:
                # Redirecionar para a HomePage
                return redirect(url_for('homepage'))
        else:
            # Exibir mensagem de Falha no Login
            flash(f'Falha no Login. E-mail ou Senha Incorretos', 'alert-danger')

    # Criou a Conta com Sucesso
    if form_criarconta.validate_on_submit() and 'botao_submit_criarconta' in request.form:
        # Criar o Usuário
        senha_criptografa = bcrypt.generate_password_hash(form_criarconta.senha.data) # Criptografar a Senha
        usuario = Usuario(username = form_criarconta.username.data, email = form_criarconta.email.data, senha = senha_criptografa)
        database.session.add(usuario) # Adicionar a sessão
        database.session.commit() # Dar um commit (salvar alterações) na sessão
        # Exibir mensagem de Conta Criada com êxito
        flash(f'Conta Criada com o e-mail: {form_criarconta.email.data}', 'alert-success')
        # Redirecionar para a Homepage
        return redirect(url_for('homepage'))

    return render_template('login.html', form_login = form_login, form_criarconta = form_criarconta)


# Sair do Perfil
@app.route('/sair')
@login_required
def sair():
    logout_user()
    flash(f'Logout feito com Sucesso', 'alert-success')
    return redirect(url_for('homepage'))


# Página de Perfil
@app.route('/perfil')
@login_required
def perfil():
    foto_perfil = url_for('static', filename = f'fotos_perfil/{current_user.foto_perfil}')
    return render_template('perfil.html', foto_perfil = foto_perfil)


# Página de Criar Post
@app.route('/post/criar', methods=['GET', 'POST'])
@login_required
def criar_post():
    form = FormCriarPost()
    if form.validate_on_submit():
        # Criar o Post
        post = Post(titulo=form.titulo.data, corpo=form.corpo.data, autor=current_user)
        database.session.add(post)
        database.session.commit()
        # Exibir mensagem de Post Criado com êxito
        flash('Post Criado com Sucesso', 'alert-success')
        # Redirecionar para a Homepage
        return redirect(url_for('homepage'))
    return render_template('criarpost.html', form=form)


# Função para Validar a Imagem
def salvar_imagem(imagem):
    # Adicionar um Código Aleatório no nome da imagem (para que ele não sobreescreva fotos anteriores)
    codigo = secrets.token_hex(8)
    nome, extensao = os.path.splitext(imagem.filename)
    nome_arquivo = nome + codigo + extensao
    caminho_completo = os.path.join(app.root_path, 'static/fotos_perfil', nome_arquivo)
    # Reduzir o Tamanho da Imagem
    tamanho = (400, 400)
    imagem_reduzida = Image.open(imagem)
    imagem_reduzida.thumbnail(tamanho)
    # Salvar a imagem na pasta foto_perfil
    imagem_reduzida.save(caminho_completo)
    return nome_arquivo

# Função para Atualizar os Cursos
def atualizar_cursos(form):
    lista_cursos = []
    for campo in form:
        if 'curso_' in campo.name:
            if campo.data:
                lista_cursos.append(campo.label.text)
    return ';'.join(lista_cursos)

# Página de Editar Perfil
@app.route('/perfil/editar', methods=['GET', 'POST'])
@login_required
def editar_perfil():
    form = FormEditarPerfil()
    # Editar o Perfil
    if form.validate_on_submit():
        current_user.email = form.email.data
        current_user.username = form.username.data
        # Verificar se a Foto de Perfil deve ser alterada
        if form.foto_perfil.data:
            # Mudar o Campo foto_perfil do Usuário para o Novo Nome da Imagem
            nome_imagem = salvar_imagem(form.foto_perfil.data)
            current_user.foto_perfil = nome_imagem
        current_user.cursos = atualizar_cursos(form)
        database.session.commit()
        # Exibir mensagem de Perfil Editado com êxito
        flash(f'Perfil atualizado com sucesso', 'alert-success')
        # Redirecionar para o Perfil
        return redirect(url_for('perfil'))
    # Fazer o Formulário já aparecer com alguns Campos Pré-preenchidos
    elif request.method == "GET":
        form.email.data = current_user.email
        form.username.data = current_user.username
    foto_perfil = url_for('static', filename=f'fotos_perfil/{current_user.foto_perfil}')
    return render_template('editarperfil.html', foto_perfil = foto_perfil, form = form)


# Página do Post Específico
@app.route('/post/<post_id>', methods=['GET', 'POST'])
@login_required
def exibir_post(post_id):
    post = Post.query.get(post_id)
    # Verificar se o Usuário é o autor do Post
    if current_user == post.autor:
        # Permitir que ele edite o Post
        form = FormCriarPost()
        # Deixar pré-preenchido
        if request.method == 'GET':
            form.titulo.data = post.titulo
            form.corpo.data = post.corpo
        # Salvar as mudanças do Post
        elif form.validate_on_submit():
            post.titulo = form.titulo.data
            post.corpo = form.corpo.data
            database.session.commit()
            # Exibir mensagem de Post Editado com Sucesso
            flash('Post Atualizado com Sucesso', 'alert-success')
            # Redirecionar para a Homepage
            return redirect(url_for('homepage'))
    else:
        form = None
    return render_template('post.html', post=post, form=form)


@app.route('/post/<post_id>/excluir', methods=['GET', 'POST'])
@login_required
def excluir_post(post_id):
    post = Post.query.get(post_id)
    # Deletar o Post
    if current_user == post.autor:
        database.session.delete(post)
        database.session.commit()
        # Exibir mensagem de Post Excluído com Sucesso
        flash('Post Excluído com Sucesso', 'alert-danger')
        # Redirecionar para a Homepage
        return redirect(url_for('homepage'))
    else:
        # Dar o Erro de Proibido (para não deixar um Usuário que não é o dono do Post Excluí-lo
        abort(403)