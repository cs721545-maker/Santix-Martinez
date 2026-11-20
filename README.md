# 𝐒antix 𝐌artinez — Windows

Primeira versão do painel desktop. A interface inclui seleção do `config.txt`, detecção das linhas VST e um controle ON/OFF com backup.

## Como gerar o EXE pelo GitHub
1. Crie um repositório no GitHub e envie todos os arquivos desta pasta.
2. Abra a aba **Actions** e execute **Build Santix Martinez for Windows** (ou faça push na branch `main`).
3. Ao terminar, baixe o artefato **Santix-Martinez-Windows**.

## Uso
1. Abra o EXE.
2. Selecione o `config.txt` real do Equalizer APO.
3. O primeiro OFF cria `config.txt.santix-backup` antes de comentar as linhas ativas.
4. ON restaura o backup exato.

**Atenção:** teste primeiro com uma cópia do arquivo e mantenha o backup. O painel não altera ganho nem presets VST. O medidor de áudio em tempo real e os controles individuais de VST ainda não estão implementados nesta primeira versão.
