FROM node:18-slim

WORKDIR /app

# Copia dependências e instala
COPY package.json .
RUN npm install

# Copia código fonte
COPY . .

EXPOSE 5173

# Inicializa o Vite com suporte a acesso externo
CMD ["npm", "run", "dev", "--", "--host"]
