class Prueba_python:
    __a: int
    __b: float
    __c: str
    def __init__(self, a, b, c):
        self.__a = a
        self.__b = b
        self.__c = c
    def mostrarT(self):
        return f"datos: {self.__a}, {self.__b}, {self.__c}"
def funcion():
    ejemplo = Prueba_python(1,2.3,"hola")
    print(ejemplo.mostrarT())
if __name__ == "__main__":
    entrada = int(input("1 para probar un objeto \n 2 para salir"))
    while isinstance(entrada, int) and entrada != 2:
        if entrada == 1:
            funcion()
        entrada = input("1 para probar un objeto \n 2 para salir")