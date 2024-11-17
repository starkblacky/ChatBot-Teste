

# Teste simples para verificar a captura de imagem
import cv2
import torch
import torchvision

if __name__ == '__main__':


    print(torch.__version__)
    print(torchvision.__version__)

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    ret, frame = cap.read()
    cap.release()
    if ret:
        cv2.imshow("Imagem Capturada", frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("Falha ao capturar a imagem")

