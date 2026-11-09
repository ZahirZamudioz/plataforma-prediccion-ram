// Avisa antes de cerrar/recargar la pestaña si hay una predicción en curso.
// La variable la mantiene un clientside callback de Dash según el estado del
// botón "Generar predicciones" (deshabilitado == generación en curso).
window.addEventListener("beforeunload", function (evento) {
    if (window.__prediccionEnCurso) {
        evento.preventDefault();
        evento.returnValue = "";
        return "";
    }
});
