/**
 * NETTOYAGE UNIFIÉ DES ERREURS
 * Fonctionne pour Contact, Devis, Inscription et Newsletter.
 */
function setupGlobalErrorCleanup() {
    // On écoute 'input' pour le texte et 'change' pour les menus déroulants (pays, statut, etc.)
    ['input', 'change'].forEach(eventType => {
        document.addEventListener(eventType, function(e) {
            const input = e.target;
            
            // On vérifie si l'élément ou son parent immédiat est marqué en erreur
            if (input.classList.contains('is-invalid')) {
                
                // 1. On retire la bordure rouge de l'input
                input.classList.remove('is-invalid');
                
                // 2. RECHERCHE DU MESSAGE D'ERREUR
                // On remonte au parent le plus large pour être sûr de trouver le message .dynamic-error-msg
                // On inclut .input-group (Contact) et .row (Devis/Téléphone)
                const container = input.closest('.mb-3, .col-md-6, .col-md-12, .col-12, .row, .input-group');
                
                if (container) {
                    // On cherche le message d'erreur dans ce conteneur
                    const errorMsg = container.querySelector('.dynamic-error-msg, .invalid-feedback');
                    if (errorMsg) {
                        // Suppression avec une petite transition fluide
                        errorMsg.style.opacity = '0';
                        setTimeout(() => errorMsg.remove(), 150);
                    }
                }
            }
        });
    });
}

// INITIALISATION UNIQUE
document.addEventListener('DOMContentLoaded', function() {
    setupGlobalErrorCleanup();
    });