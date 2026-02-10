// --- LOGIQUE DE NAVIGATION ---
//
function setupLiveErrorCleanup() {
    // On écoute l'événement 'input' (quand on tape) sur tout le document
    document.addEventListener('input', function(e) {
        const input = e.target;
        
        // On ne traite que les éléments qui ont la classe d'erreur
        if (input.classList.contains('is-invalid')) {
            
            // 1. On retire la bordure rouge de l'input
            input.classList.remove('is-invalid');
            
            // 2. On remonte au parent qui contient l'input ET le message d'erreur
            // On cible les conteneurs de colonnes ou de groupes de ton HTML
            const container = input.closest('.col-md-6, .col-md-12, .col-12, .mb-3');
            
            if (container) {
                // On cherche tous les messages d'erreur possibles dans ce conteneur
                const errorMessages = container.querySelectorAll('.dynamic-error-msg, .invalid-feedback');
                
                errorMessages.forEach(msg => {
                    // On ajoute une petite animation de sortie (optionnel)
                    msg.style.opacity = '0';
                    msg.style.transition = 'opacity 0.2s ease';
                    // On supprime après l'animation
                    setTimeout(() => msg.remove(), 200);
                });
            }
        }
    });
}

function showStep(step) {
    document.querySelectorAll('[id^="step"]').forEach(s => s.classList.add('hidden'));
    const targetStep = document.getElementById('step' + step);
    if (targetStep) {
        targetStep.classList.remove('hidden');
        targetStep.classList.add('fade-in');
    }
    updateProgressBar(step);
    window.scrollTo({ top: 100, behavior: 'smooth' });
}

function updateProgressBar(step) {
    for (let i = 1; i <= 4; i++) {
        const s = document.getElementById('s' + i);
        const l = document.getElementById('l' + i);
        if (s) s.classList.toggle('active', i <= step);
        if (l) l.classList.toggle('active', i < step);
    }
}

function nextStep(step) {
    // On valide l'étape précédente avant de passer à la suivante
    if (validateStepInputs(step - 1)) {
        showStep(step);
    }
}

function prevStep(step) {
    showStep(step);
}

// --- LOGIQUE DE VALIDATION LOCALE ---

function validateStepInputs(stepNum) {
    const container = document.getElementById('step' + stepNum);
    if (!container) return true;

    const inputs = container.querySelectorAll('input, select, textarea');
    let isValid = true;

    inputs.forEach(input => {
        if (input.type === 'hidden' || input.type === 'submit') return;

        // Reset visuel
        input.classList.remove('is-invalid');
        const parentDiv = input.closest('.mb-3, .col-md-6, .col-md-12, .col-md-4, .col-md-8, .col-12');
        const existingMsg = parentDiv?.querySelector('.dynamic-error-msg');
        if (existingMsg) existingMsg.remove();

        let errorMessage = "";

        // 1. Vide
        if (!input.value.trim()) {
            errorMessage = "Ce champ est obligatoire.";
        } 
        // 2. Email
        else if (input.type === 'email') {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(input.value)) {
                errorMessage = "Veuillez entrer une adresse email valide.";
            }
        }
        // 3. Téléphone (min 8)
        else if (input.name === 'phone' && input.value.length < 8) {
            errorMessage = "Le numéro est trop court.";
        }
        // 4. Mots de passe (Step 4)
        if (stepNum === 4) {
            const p1 = document.querySelector('input[name="password1"]');
            const p2 = document.querySelector('input[name="password2"]');
            
            if (input.name === "password1" && input.value.length < 8) {
                errorMessage = "Le mot de passe doit contenir au moins 8 caractères.";
            }
            if (input.name === "password2" && p1.value !== p2.value) {
                errorMessage = "Les mots de passe ne correspondent pas.";
            }
        }

        if (errorMessage) {
            isValid = false;
            input.classList.add('is-invalid');
            const errorMsg = document.createElement('div');
            
            errorMsg.className = 'text-danger small mt-1 dynamic-error-msg animate__animated animate__fadeInUp';
            errorMsg.innerText = errorMessage;
            
            const placement = input.closest('.input-group') || input.closest('.row.g-0') || input;
            placement.after(errorMsg);
        }
    });
    return isValid;
}

// --- SYSTÈME AJAX & RETOUR SERVEUR ---

document.addEventListener('DOMContentLoaded', function() {
        setupLiveErrorCleanup();

    const handleFieldValidation = (form, errors) => {
        // On nettoie d'abord
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.dynamic-error-msg').forEach(el => el.remove());

        if (!errors) return;

        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');
                // Récupération du message (Django renvoie souvent une liste)
                const errorMessage = Array.isArray(errors[fieldName]) ? errors[fieldName][0] : errors[fieldName];
                // Affichage du message
                // TRADUCTION À LA VOLÉE (Si non fait en Python)
            if (errorMessage.includes("already exists")) errorMessage = "Cet email est déjà utilisé.";
            if (errorMessage.includes("too common")) errorMessage = "Ce mot de passe est trop commun.";
            if (errorMessage.includes("too short")) errorMessage = "Le mot de passe est trop court.";
            
                const newError = document.createElement('div');
                newError.className = 'text-danger small mt-1 dynamic-error-msg animate__animated animate__fadeIn';
                newError.innerText = errorMessage;
                
                const placement = field.closest('.input-group') || field.closest('.row.g-0') || field;
                placement.after(newError);
                
                
            }
        });

        // Téléportation intelligente vers l'étape contenant l'erreur
        if (form.querySelector('#step1 .is-invalid')) showStep(1);
        else if (form.querySelector('#step2 .is-invalid')) showStep(2);
        else if (form.querySelector('#step3 .is-invalid')) showStep(3);
        else if (form.querySelector('#step4 .is-invalid')) showStep(4);
    };

    const setupAjaxForm = (formId, messageId) => {
        const form = document.getElementById(formId);
        if (!form) return;

        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Validation de tous les steps avant l'envoi final
            let firstErrorStep = null;
            for(let i=1; i<=4; i++) {
                if (!validateStepInputs(i) && !firstErrorStep) {
                    firstErrorStep = i;
                }
            }

            if (firstErrorStep) {
                showStep(firstErrorStep);
                return;
            }

            const responseDiv = document.getElementById(messageId);
            const submitBtn = form.querySelector('[type="submit"]');
            const formData = new FormData(this);

            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Envoi...';
            }
            
            fetch(this.action || window.location.href, {
                method: 'POST',
                body: formData,
                headers: { 'X-Requested-With': 'XMLHttpRequest', 'X-CSRFToken': formData.get('csrfmiddlewaretoken') }
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    responseDiv.innerHTML = `<div class="alert alert-success py-2 animate__animated animate__bounceIn">${data.message}</div>`;
                    setTimeout(() => window.location.href = data.redirect_url, 2000);
                } else {
                    responseDiv.innerHTML = `<div class="alert alert-danger py-2 small">Veuillez corriger les erreurs.</div>`;
                    if (data.errors) handleFieldValidation(form, data.errors);
                }
            })
            .catch(err => {
                responseDiv.innerHTML = '<div class="alert alert-danger py-2 small">Erreur de connexion serveur.</div>';
            })
            .finally(() => { 
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerText = 'Soumettre ma candidature';
                }
            });
        });
    };

    setupAjaxForm('mentorForm', 'register-message');
    
    // Au démarrage, on affiche le step 1 ou celui avec erreur
    showStep(1); 
});

