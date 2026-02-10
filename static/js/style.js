// faq page party 
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('#faq-filters .btn-faq-filter');
    const faqItems = document.querySelectorAll('.faq-item');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 1. Gérer la classe active sur les boutons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            // 2. Récupérer le filtre sélectionné
            const filterValue = this.getAttribute('data-filter');

            // 3. Filtrer les éléments FAQ
            faqItems.forEach(item => {
                const itemCategory = item.getAttribute('data-category');
                
                if (filterValue === 'all' || itemCategory === filterValue) {
                    item.style.display = 'block'; // Afficher
                } else {
                    item.style.display = 'none'; // Masquer
                }
            });
        });
    });
});


// function nextStep(step) {
//     const currentStepDiv = document.querySelector(`#step${step - 1}`);
    
//     // Validation des champs requis avant de continuer
//     const inputs = currentStepDiv.querySelectorAll("[required]");
//     let isValid = true;
    
//     inputs.forEach(input => {
//         if (!input.checkValidity()) {
//             input.reportValidity(); // Affiche l'erreur native du navigateur
//             input.classList.add("is-invalid");
//             isValid = false;
//         } else {
//             input.classList.remove("is-invalid");
//         }
//     });

//     if (isValid) {
//         // Masquage et affichage avec animation
//         document.querySelectorAll('[id^="step"]').forEach(div => {
//             div.classList.add('hidden');
//             div.classList.remove('fade-in');
//         });
        
//         const nextDiv = document.getElementById(`step${step}`);
//         nextDiv.classList.remove('hidden');
//         nextDiv.classList.add('fade-in');

//         // Mise à jour de la barre de progression
//         updateProgress(step);
//     }
// }

// function prevStep(step) {
//     document.querySelectorAll('[id^="step"]').forEach(div => div.classList.add('hidden'));
//     const prevDiv = document.getElementById(`step${step}`);
//     prevDiv.classList.remove('hidden');
//     prevDiv.classList.add('fade-in');

//     updateProgress(step, true);
// }

// function updateProgress(step, goingBack = false) {
//     if (!goingBack) {
//         // En avançant
//         document.getElementById(`s${step}`).classList.add('active');
//         document.getElementById(`l${step - 1}`).classList.add('active');
//         document.getElementById(`s${step - 1}`).classList.replace('active', 'completed');
//         document.getElementById(`s${step - 1}`).innerHTML = '✓'; // Petit effet "terminé"
//     } else {
//         // En reculant
//         document.getElementById(`s${step + 1}`).classList.remove('active');
//         document.getElementById(`l${step}`).classList.remove('active');
//         document.getElementById(`s${step}`).classList.replace('completed', 'active');
//         document.getElementById(`s${step}`).innerHTML = step;
//     }
// }

//

    document.addEventListener('DOMContentLoaded', function() {
        
        /**
         * Gère l'affichage visuel des erreurs (Bordures rouges + messages)
         * Cette fonction évite la répétition pour tous vos formulaires.
         */
    //     const setupLiveErrorCleanup = () => {
    //     document.addEventListener('input', function(e) {
    //         const input = e.target;
    //         if (input.classList.contains('is-invalid')) {
    //             input.classList.remove('is-invalid');
    //             // On remonte au conteneur parent pour supprimer le message
    //             const container = input.closest('.mb-3, .col-md-6, .col-md-12, .col-12, .row');
    //             const errorMsg = container?.querySelector('.dynamic-error-msg');
    //             if (errorMsg) errorMsg.remove();
    //         }
    //     });
    // };
    const setupLiveErrorCleanup = () => {
    // On écoute sur le document pour couvrir tous les formulaires (délégation d'événement)
    document.addEventListener('input', function(e) {
        const field = e.target;
        
        // Si le champ a la classe d'erreur
        if (field.classList.contains('is-invalid')) {
            // 1. Retirer la bordure rouge du champ
            field.classList.remove('is-invalid');
            
            // 2. Chercher et supprimer le message d'erreur textuel
            // On cherche d'abord dans le parent direct (mb-3, col, etc.)
            const container = field.closest('.mb-3, .col-md-6, .col-md-12, .col-12, .row, .input-group');
            if (container) {
                const errorMsg = container.querySelector('.dynamic-error-msg, .invalid-feedback');
                if (errorMsg) {
                    errorMsg.innerHTML = ''; // On vide le texte
                    // Si c'est un élément créé dynamiquement (div), on peut aussi le remove
                    if (errorMsg.classList.contains('dynamic-error-msg')) {
                        errorMsg.remove();
                    }
                }
            }
        }
    });
};
        const handleFieldValidation = (form, errors) => {
        // 1. NETTOYAGE
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.dynamic-error-msg, .invalid-feedback, .text-danger.small').forEach(el => {
            if (!el.classList.contains('form-label')) el.innerHTML = '';
        });

        if (!errors) return;

        // 2. INJECTION
        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');

                // On cherche un conteneur existant dans le parent col-md ou mb-3
                let errorContainer = field.closest('.mb-3, .col-md-6, .col-md-12, .col-md-4')?.querySelector('.text-danger.small, .invalid-feedback');
                
                const errorMessage = errors[fieldName][0].message;

                if (errorContainer) {
                    errorContainer.innerHTML = errorMessage;
                    errorContainer.classList.add('dynamic-error-msg');
                } else {
                    const newError = document.createElement('div');
                    newError.className = 'text-danger small mt-1 dynamic-error-msg';
                    newError.innerText = errorMessage;
                    
                    // AJUSTEMENT ICI : On gère l'input-group (Contact) OU la row g-0 (Inscription/Devis)
                    const placement = field.closest('.input-group') || field.closest('.row.g-0') || field;
                    placement.after(newError);
                }
            }
        });

        // LOGIQUE MULTI-ÉTAPES (Spécifique à l'inscription)
        // Si on a des erreurs, on redirige l'utilisateur vers la première étape qui contient un champ rouge
        if (form.id === 'registration-form') { 
            if (form.querySelector('#step1 .is-invalid')) nextStep(1);
            else if (form.querySelector('#step2 .is-invalid')) nextStep(2);
            else if (form.querySelector('#step3 .is-invalid')) nextStep(3);
            else if (form.querySelector('#step4 .is-invalid')) nextStep(4);
        }


    };

        /**
         * Fonction principale AJAX
         */
        const setupAjaxForm = (formSelector, messageSelector) => {
            const forms = document.querySelectorAll(formSelector);

            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    e.preventDefault();

                    const responseDiv = messageSelector ? document.querySelector(messageSelector) : form.querySelector('.ajax-response');
                    const submitBtn = form.querySelector('[type="submit"]');
                    const formData = new FormData(this);
                    const csrftoken = form.querySelector('[name=csrfmiddlewaretoken]')?.value;

                    if (submitBtn) submitBtn.disabled = true;
                    if (responseDiv) responseDiv.innerHTML = '<span class="text-muted small">Traitement en cours...</span>';

                    fetch(this.action || window.location.href, {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-Requested-With': 'XMLHttpRequest',
                            'X-CSRFToken': csrftoken
                        }
                    })
                    .then(response => response.json().then(data => ({ status: response.status, body: data })))
                    .then(({ status, body }) => {
                        const isSuccess = body.status === 'success';

                        // Affichage du message global (Success ou Error)
                        if (responseDiv) {
                            const alertClass = isSuccess ? 'alert-success' : 'alert-danger';
                            const icon = isSuccess ? 'fa-check-circle' : 'fa-exclamation-circle';
                            responseDiv.innerHTML = `<div class="alert ${alertClass} py-2 small animate__animated animate__fadeIn">
                                <i class="fas ${icon} me-1"></i> ${body.message}
                            </div>`;
                        }

                        if (isSuccess) {
                            form.reset();
                            handleFieldValidation(form, null); // Nettoie le rouge
                        } else {
                            if (body.errors) {
                                handleFieldValidation(form, body.errors); // Affiche le rouge
                            }
                        }
                    })
                    .catch(error => {
                        console.error('AJAX Error:', error);
                        if (responseDiv) responseDiv.innerHTML = '<div class="alert alert-danger py-2 small">Erreur technique de connexion.</div>';
                    })
                    .finally(() => {
                        if (submitBtn) submitBtn.disabled = false;
                    });
                });
                const btn = form.querySelector('[type="submit"]');
if (btn) btn.disabled = false; // On réactive le bouton seulement quand le JS est prêt
            });
        };

        // --- INITIALISATION UNIQUE ---
        setupLiveErrorCleanup(); // <--- AJOUTE CET APPEL ICI !
        setupAjaxForm('#contact-form', '#contact-message');
        setupAjaxForm('#ajax-devis-form', '#devis-message'); // Ajoutez id="devis-message" dans votre template devis
        setupAjaxForm('#newsletter-form', '#newsletter-message');
        setupAjaxForm('#form-souscription','#souscription-message')
    });
//FAQ PARTY
document.addEventListener('DOMContentLoaded', function() {
    const filterButtons = document.querySelectorAll('.btn-faq-filter');
    const faqItems = document.querySelectorAll('.faq-item');

    filterButtons.forEach(button => {
        button.addEventListener('click', function() {
            // 1. Gestion de l'état actif des boutons
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const filterValue = this.getAttribute('data-filter');

            // 2. Logique de filtrage
            faqItems.forEach(item => {
                if (filterValue === 'all' || item.getAttribute('data-category') === filterValue) {
                    item.style.display = 'block';
                    // Animation optionnelle
                    item.style.opacity = '0';
                    setTimeout(() => { item.style.opacity = '1'; item.style.transition = '0.4s'; }, 10);
                } else {
                    item.style.display = 'none';
                }
            });
        });
    });
// });

});

//
document.addEventListener('DOMContentLoaded', function() {
    
    const setupAjaxForm = (formSelector, messageSelector) => {
        const forms = document.querySelectorAll(formSelector);

        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                e.preventDefault(); // Empêche le rechargement et la fermeture du modal

                const responseDiv = messageSelector ? document.querySelector(messageSelector) : form.querySelector('.ajax-response');
                const submitBtn = form.querySelector('[type="submit"]');
                const formData = new FormData(this);
                const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

                // UI : Reset des erreurs précédentes
                form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
                form.querySelectorAll('.invalid-feedback').forEach(el => el.remove());
                
                if (submitBtn) submitBtn.disabled = true;
                if (responseDiv) responseDiv.innerHTML = '<span class="text-muted small">Traitement...</span>';

                fetch(this.action, {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    }
                })
                .then(response => response.json().then(data => ({ status: response.status, body: data })))
                .then(({ status, body }) => {
                    if (status === 200) {
                        // SUCCÈS
                        responseDiv.innerHTML = `<span class="text-success small fw-bold"><i class="fas fa-check-circle me-1"></i> ${body.message}</span>`;
                        form.reset();
                        // Optionnel : fermer le modal après un délai
                        // setTimeout(() => { bootstrap.Modal.getInstance(form.closest('.modal')).hide(); }, 2000);
                    } else {
                        // ERREUR DE VALIDATION (400)
                        responseDiv.innerHTML = `<span class="text-danger small fw-bold"><i class="fas fa-exclamation-circle me-1"></i> ${body.message}</span>`;
                        
                        if (body.errors) {
                            displayFormErrors(form, body.errors);
                        }
                    }
                })
                .catch(error => {
                    responseDiv.innerHTML = `<span class="text-danger small fw-bold">Erreur technique de connexion.</span>`;
                })
                .finally(() => {
                    if (submitBtn) submitBtn.disabled = false;
                });
            });
        });
    };

    /**
     * Fonction pour injecter les erreurs dans les champs Bootstrap
     */
    function displayFormErrors(form, errors) {
        Object.keys(errors).forEach(fieldName => {
            const inputField = form.querySelector(`[name="${fieldName}"]`);
            if (inputField) {
                // Ajouter la classe rouge de Bootstrap
                inputField.classList.add('is-invalid');

                // Créer le message d'erreur
                const errorDiv = document.createElement('div');
                errorDiv.className = 'invalid-feedback';
                errorDiv.innerText = errors[fieldName][0].message;

                // Placement intelligent de l'erreur
                if (inputField.parentElement.classList.contains('input-group')) {
                    inputField.parentElement.after(errorDiv);
                    errorDiv.style.display = 'block'; 
                } else {
                    inputField.after(errorDiv);
                }
            }
        });
    }

    // Initialisation
setupAjaxForm('#consultation-form', '#consultation-message');
});