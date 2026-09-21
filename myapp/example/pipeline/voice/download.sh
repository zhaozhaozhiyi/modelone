: "${MODELONE_ASSET_BASE_URL:?Set the enterprise resource base URL}"
wget ${MODELONE_ASSET_BASE_URL%/}/pipeline/LibriSpeech.zip
unzip LibriSpeech.zip
