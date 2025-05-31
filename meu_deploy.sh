#!/bin/bash

# --- Constantes de Configuração (Ajuste se necessário) ---
# Seu nome de usuário no Docker Hub (será perguntado se estiver vazio)
DOCKERHUB_USER="rodrigobahia" # <<-- COLOQUE SEU USUÁRIO DO DOCKER HUB AQUI OU DEIXE VAZIO PARA SER PERGUNTADO
# Nome da imagem no Docker Hub (sem o seu usuário na frente)
REMOTE_IMAGE_NAME="lotofacil-web"
# Nome do serviço no seu docker-compose.yml (usamos 'web')
COMPOSE_SERVICE_NAME="web"
# Nome do remote do Git (geralmente 'origin')
GIT_REMOTE_NAME="origin"
# Nome da branch principal do Git (geralmente 'main')
GIT_BRANCH_NAME="main"

# --- Funções Auxiliares ---
print_header() {
    echo ""
    echo "===================================================================="
    echo "  $1"
    echo "===================================================================="
    echo ""
}

ask_yes_no() {
    # $1 é a mensagem da pergunta
    while true; do
        read -p "$1 [s/N]: " yn
        case $yn in
            [Ss]* ) return 0;;  # Sim
            [Nn]* ) return 1;;  # Não
            * ) echo "Por favor, responda 's' para sim ou 'n' para não.";;
        esac
    done
}

# --- Início do Script ---
# Pega o nome da pasta atual, que o Docker Compose usa para nomear a imagem local
PROJECT_DIR_NAME=$(basename "$PWD")
LOCAL_IMAGE_NAME_GUESS="${PROJECT_DIR_NAME}-${COMPOSE_SERVICE_NAME}" # Ex: lotofacil_web-web

clear
print_header "🚀 Assistente Interativo de Deploy - Lotofácil Web 🚀"
echo "Este script vai te guiar pelo processo de:"
echo "1. Versionamento com Git (commit e push)."
echo "2. Construção e envio da imagem Docker para o Docker Hub."
echo "3. Lembretes para o deploy na VPS via Portainer."
echo ""
echo "Pressione Enter para avançar em alguns passos ou 'n' para pular."
echo ""

# --- ETAPA 1: GIT WORKFLOW ---
print_header "Etapa 1: Versionamento com Git"
echo "Verificando o status do seu repositório Git..."
git status
echo ""

if ask_yes_no "Você fez alterações no código e deseja registrá-las no Git?"; then
    echo "--------------------------------------------------------------------"
    echo "Adicionando todas as alterações ao 'palco' (git add .)..."
    read -p "Pressione Enter para continuar ou 'n' para pular esta etapa: " choice
    if [[ "$choice" != "n" && "$choice" != "N" ]]; then
        git add .
        echo "✅ Alterações adicionadas!"
        git status # Mostrar o status novamente
        echo ""
        
        echo "Agora, vamos fazer o 'commit' (salvar um snapshot das mudanças)."
        read -p "Digite sua mensagem de commit (ex: 'Adiciona nova feature X'): " commit_message
        
        if [ -z "$commit_message" ]; then
            echo "⚠️ Mensagem de commit vazia. Commit cancelado."
        else
            git commit -m "$commit_message"
            echo "✅ Commit realizado com sucesso!"
            echo ""
            if ask_yes_no "Deseja enviar (push) estas alterações para o GitHub ($GIT_REMOTE_NAME/$GIT_BRANCH_NAME) agora?"; then
                git push $GIT_REMOTE_NAME $GIT_BRANCH_NAME
                echo "✅ Alterações enviadas para o GitHub!"
            else
                echo "↪️ Lembre-se de fazer o 'git push' mais tarde."
            fi
        fi
    else
        echo "↪️ Etapa 'git add' pulada."
    fi
else
    echo "👍 Ok, nenhuma alteração a ser registrada no Git por enquanto."
fi

# --- ETAPA 2: DOCKER IMAGE WORKFLOW ---
print_header "Etapa 2: Imagem Docker"
if ask_yes_no "Deseja construir uma nova imagem Docker e enviá-la para o Docker Hub?"; then
    echo "--------------------------------------------------------------------"
    echo "Construindo a imagem Docker com 'docker compose build'..."
    echo "Isso pode levar um tempo se for a primeira vez ou se houver muitas mudanças."
    read -p "Pressione Enter para continuar ou 'n' para pular esta etapa: " choice
    if [[ "$choice" != "n" && "$choice" != "N" ]]; then
        docker compose build
        echo "✅ Build da imagem Docker concluído!"
        echo ""
        
        echo "Agora precisamos 'etiquetar' (tag) a imagem construída para o Docker Hub."
        echo "O Docker Compose geralmente nomeia a imagem local como '${LOCAL_IMAGE_NAME_GUESS}:latest'."
        echo "Se for diferente, você precisará ajustar o comando de tag manualmente depois."
        
        # Pergunta pelo usuário do Docker Hub se não estiver configurado
        if [ -z "$DOCKERHUB_USER" ]; then
            read -p "Qual é o seu nome de usuário no Docker Hub? " DOCKERHUB_USER_INPUT
            if [ -n "$DOCKERHUB_USER_INPUT" ]; then
                DOCKERHUB_USER=$DOCKERHUB_USER_INPUT
            fi
        fi
        
        if [ -z "$DOCKERHUB_USER" ]; then
            echo "⚠️ Nome de usuário do Docker Hub não fornecido. Pulando etiquetagem e push."
        else
            FULL_REMOTE_IMAGE_NAME="${DOCKERHUB_USER}/${REMOTE_IMAGE_NAME}:latest"
            echo "Vamos etiquetar a imagem local '${LOCAL_IMAGE_NAME_GUESS}:latest' como '${FULL_REMOTE_IMAGE_NAME}'."
            read -p "Pressione Enter para continuar ou 'n' para pular: " choice_tag
            if [[ "$choice_tag" != "n" && "$choice_tag" != "N" ]]; then
                docker tag "${LOCAL_IMAGE_NAME_GUESS}:latest" "${FULL_REMOTE_IMAGE_NAME}"
                echo "✅ Imagem etiquetada!"
                echo ""
                echo "Agora, vamos enviar (push) a imagem '${FULL_REMOTE_IMAGE_NAME}' para o Docker Hub."
                echo "Pode ser que ele peça seu login do Docker Hub se sua sessão expirou."
                echo "Lembrete: Para login manual, use 'docker login' em outro terminal."
                read -p "Pressione Enter para continuar ou 'n' para pular: " choice_push
                if [[ "$choice_push" != "n" && "$choice_push" != "N" ]]; then
                    docker push "${FULL_REMOTE_IMAGE_NAME}"
                    echo "✅ Imagem enviada para o Docker Hub!"
                else
                    echo "↪️ 'docker push' pulado."
                fi
            else
                echo "↪️ Etiquetagem e push pulados."
            fi
        fi
    else
        echo "↪️ Build da imagem Docker pulado."
    fi
else
    echo "👍 Ok, nenhuma ação para a imagem Docker por enquanto."
fi

# --- ETAPA 3: LEMBRETE DE DEPLOY NA VPS ---
print_header "Etapa 3: Deploy na VPS com Portainer (Lembrete)"
if [ -n "$DOCKERHUB_USER" ]; then
    echo "Se você enviou uma nova imagem para o Docker Hub (${DOCKERHUB_USER}/${REMOTE_IMAGE_NAME}:latest),"
    echo "não se esqueça de atualizar sua aplicação na VPS através do Portainer:"
    echo ""
    echo "1. Acesse sua interface do Portainer."
    echo "2. Vá em 'Stacks' e selecione o stack da sua aplicação Lotofácil (o do tipo 'Enxame')."
    echo "3. Clique na aba 'Editor'."
    echo "4. Certifique-se que a linha 'image:' está correta:"
    echo "   image: ${DOCKERHUB_USER}/${REMOTE_IMAGE_NAME}:latest"
    echo "5. Marque a opção 'Re-pull image' (ou 'Pull latest image versions') se disponível."
    echo "6. Clique em 'Update the stack' (ou botão similar)."
    echo ""
    echo "O Portainer cuidará de baixar a nova imagem e reiniciar o serviço."
else
    echo "Como não fizemos o push da imagem Docker, lembre-se de fazê-lo antes de atualizar na VPS."
fi

print_header "🎉 Assistente Finalizado! 🎉"
echo "Este script é um guia. Use-o como base para o seu fluxo de trabalho."