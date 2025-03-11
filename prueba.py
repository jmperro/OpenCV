from tkinter import Frame, Tk, Label, Button, filedialog
import cv2
import pytesseract

# Configura la ruta de Tesseract si es necesario (solo en Windows)
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def preprocess_image(image_path):
	"""
	Preprocesa la imagen: la convierte a escala de grises, aplica un desenfoque y un umbral.
	"""
	# Cargar la imagen
	image = cv2.imread(image_path)
	if image is None:
		raise ValueError("No se pudo cargar la imagen. Verifica la ruta.")

	# Convertir a escala de grises
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# Aplicar un desenfoque para reducir el ruido
	# blurred = cv2.GaussianBlur(gray, (5, 5), 0)
	blurred = cv2.GaussianBlur(gray, (3, 3), 0)

	# Aplicar umbral adaptativo para mejorar detección
	binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
	# binary = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 10)
	
	cv2.imwrite("binary_debug1.jpg", binary)
	
	# Operación morfológica para cerrar los bordes de las casillas
	kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
	# kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
	binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)
	
	cv2.imwrite("binary_debug2.jpg", binary)

	return image, binary

def detect_checkboxes(image, binary_image):
	"""
	Detecta las casillas en la imagen binaria usando cv2.findContours().
	"""
	# Encontrar contornos en la imagen binaria
	contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

	checkboxes = []
	for contour in contours:
		x, y, w, h = cv2.boundingRect(contour)
		aspect_ratio = w / float(h)
		
		# Filtrar contornos que tengan forma cuadrada (posibles casillas de verificación)
		if 0.8 <= aspect_ratio <= 1.2 and 15 <= w <= 40 and 15 <= h <= 40:
			checkboxes.append((x, y, w, h))
			cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)


	# for contour in contours:
	# 	# Aproximar el contorno a un polígono
	# 	epsilon = 0.04 * cv2.arcLength(contour, True)
	# 	approx = cv2.approxPolyDP(contour, epsilon, True)
		
	# 	# Solo considerar contornos con 4 lados (cuadriláteros)
	# 	if len(approx) == 4:
	# 		x, y, w, h = cv2.boundingRect(approx)
	# 		aspect_ratio = w / float(h)
			
	# 		# Filtrar por tamaño y relación de aspecto
	# 		if 20 <= w <= 70 and 20 <= h <= 70 and 0.7 <= aspect_ratio <= 1.3:
	# 			checkboxes.append((x, y, w, h))

	return checkboxes

def extract_checkboxes(image, binary_image, checkboxes):
	"""
	Extrae las casillas detectadas y verifica si están marcadas con una X.
	"""
	results = []
	for (x, y, w, h) in checkboxes:
		# Recortar la casilla
		checkbox = binary_image[y:y + h, x:x + w]

		# Verificar si la casilla está marcada (contar píxeles blancos)
		white_pixels = cv2.countNonZero(checkbox)
		total_pixels = checkbox.size
		if total_pixels > 0 and (white_pixels / total_pixels) > 0.6:
			results.append((x, y, w, h, "Marcado"))
		else:
			results.append((x, y, w, h, "No marcado"))

	return results

def recognize_text(image):
	"""
	Reconoce el texto en la imagen usando Pytesseract.
	"""
	# Convertir la imagen a escala de grises para OCR
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

	# Aplicar OCR
	text = pytesseract.image_to_string(gray, config='--psm 3')
	return text

def main(image_path):
	# Preprocesar la imagen
	image, binary = preprocess_image(image_path)

	# Detectar casillas
	checkboxes = detect_checkboxes(image, binary)
	if not checkboxes:
		print("No se detectaron casillas.")
		return

	# Extraer y verificar casillas
	checkbox_results = extract_checkboxes(image, binary, checkboxes)

	# Mostrar resultados
	for i, (x, y, w, h, status) in enumerate(checkbox_results):
		print(f"Casilla {i + 1}: {status}")
		if status == "Marcado":
			cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
		else:
			cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)


	# Reconocer texto
	# text = recognize_text(image)
	# print("Texto reconocido:")
	# print(text)

	# Mostrar la imagen con las casillas detectadas
	window_name = "Checkboxes detected"

	cv2.imwrite("result.jpg", image)
	cv2.imshow(window_name, image)

	# Obtener la posición de la ventana principal de Tkinter
	root.update_idletasks()  # Asegura que Tkinter actualice la posición de la ventana
	
	# Obtener la posición y tamaño de la ventana principal de Tkinter
	tk_x = root.winfo_x()
	tk_y = root.winfo_y()
	tk_width = root.winfo_width()
	tk_height = root.winfo_height()

	# Obtener tamaño de la imagen mostrada (o usar un tamaño fijo)
	img_height, img_width = image.shape[:2]

	# Calcular la posición para centrar la ventana de OpenCV en la misma pantalla que Tkinter
	position_x = tk_x + (tk_width - img_width) // 2
	position_y = tk_y + (tk_height - img_height) // 2

	# Mover la ventana de OpenCV al centro de la ventana principal
	cv2.moveWindow(window_name, position_x, position_y)

	cv2.waitKey(0)
	cv2.destroyAllWindows()

def load_image():
	"""
	Abre un cuadro de diálogo para que el usuario seleccione una imagen.
	"""
	file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.jpeg;*.png")])
	if file_path:
		main(file_path)

# Ejecutar el programa
if __name__ == "__main__":
	root = Tk()
	root.title("Questionnaire Reader")

	# Establezco el tamaño de la ventana
	window_width = 320
	window_height = 240

	# Obtener tamaño de la pantalla
	screen_width = root.winfo_screenwidth()
	screen_height = root.winfo_screenheight()

	# Calcular posición para centrar la ventana
	position_x = (screen_width - window_width) // 2
	position_y = (screen_height - window_height) // 2

	# Establecer tamaño y posición de la ventana
	root.geometry(f"{window_width}x{window_height}+{position_x}+{position_y}")
	
	# Crear un Frame para centrar los elementos verticalmente
	frame = Frame(root)
	frame.pack(expand=True)  # expand=True permite que el frame ocupe el espacio vertical disponible

	# Contenido de la ventana dentro del frame
	Label(frame, text="Load Image").pack(pady=10)  # Añade espacio vertical
	Button(frame, text="Load", command=load_image).pack()
	
	root.mainloop()