# ComfyUI Open in Blender

Custom node que recebe uma malha `MESH`, abre o Blender e importa a geometria
em uma cena nova. O node também leva UVs, texturas e materiais incluídos na
malha.

## Instalação

Coloque esta pasta em `ComfyUI/custom_nodes/Comfyui-open-in-blender` e reinicie
o ComfyUI.

Instale o Blender para Windows. O node procura `blender.exe` no `PATH`, nas
entradas de instalação do Windows e nas pastas usuais do Blender. Se ele não
for encontrado automaticamente, configure a variável de ambiente `BLENDER_EXE`
com o caminho completo para `blender.exe` e reinicie o ComfyUI.

## Uso

Adicione `Open in Blender` ao workflow e conecte a saída `MESH` ao node. Como é
um node de ação sem saída, ele abre uma janela do Blender e importa a malha em
uma cena vazia. Para lotes `MESH`, cada item é importado na mesma cena.

O node exporta a malha temporariamente como GLB usando o serializador nativo do
ComfyUI. Depois que o Blender importa a geometria, os arquivos temporários são
removidos automaticamente.

## Requisitos

- Windows.
- ComfyUI e Blender instalados.
- O serializador `mesh_item_to_glb_bytes` fornecido pelo ComfyUI.

Não são necessárias dependências Python adicionais.
