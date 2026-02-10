   // --- LOGIQUE MULTI-ÉTAPES ---
// --- LOGIQUE MULTI-ÉTAPES ---
function setupLiveErrorCleanup() {
    // Écoute les entrées clavier (input) et les changements (select/change)
    ['input', 'change'].forEach(eventType => {
        document.addEventListener(eventType, function(e) {
            const input = e.target;
            
            // Si le champ est en mode "erreur"
            if (input.classList.contains('is-invalid')) {
                // 1. On retire la bordure rouge
                input.classList.remove('is-invalid');
                
                // 2. On cible le parent qui contient l'input et l'erreur (structure Bootstrap)
                const container = input.closest('.mb-3, .col-md-6, .col-md-12, .col-md-4, .col-md-8, .col-12, .input-group');
                
                if (container) {
                    // On cherche tous les messages d'erreur générés dynamiquement
                    const errorMessages = container.querySelectorAll('.dynamic-error-msg, .invalid-feedback');
                    errorMessages.forEach(msg => {
                        msg.style.opacity = '0';
                        msg.style.transition = 'opacity 0.2s ease';
                        setTimeout(() => msg.remove(), 200);
                    });
                }
            }
        });
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
    // On remonte légèrement au dessus du titre de l'étape
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

/**
 * VALIDE LES INPUTS D'UNE ÉTAPE AVEC VALIDATION EMAIL LOCALE
 */
function validateStepInputs(stepNum) {
    const container = document.getElementById('step' + stepNum);
    if (!container) return true;

    const inputs = container.querySelectorAll('input, select');
    let isValid = true;
    const optionalFields = [];

    inputs.forEach(input => {
        if (optionalFields.includes(input.name) || input.type === 'hidden' || input.type === 'submit') return;

        // Reset visuel
        input.classList.remove('is-invalid');
        const parentDiv = input.closest('.mb-3, .col-md-6, .col-md-12, .col-md-4, .col-md-8');
        const existingMsg = parentDiv?.querySelector('.dynamic-error-msg');
        if (existingMsg) existingMsg.remove();

        let errorMessage = "";

        // 1. Validation : Vide
        if (!input.value.trim()) {
            errorMessage = "Ce champ est obligatoire.";
        } 
        // 2. Validation : Format Email (uniquement si le champ est de type email)
        else if (input.type === 'email') {
            const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailPattern.test(input.value)) {
                errorMessage = "Veuillez entrer une adresse email valide (ex: nom@domaine.com).";
            }
        }
        // 2. Vérification spécifique au Step 4 (Mots de passe)
        if (stepNum === 4) {
            const pass1 = container.querySelector('input[name="password1"]');
            const pass2 = container.querySelector('input[name="password2"]');

            if (input.name === "password2" && pass1.value !== pass2.value) {
                errorMessage = "Les mots de passe ne correspondent pas.";
            }
        }
        // À l'intérieur de la boucle inputs.forEach de validateStepInputs
if (input.name === "password1" && input.value.trim() !== "") {
    if (input.value.length < 8) {
        isValid = false;
        errorMessage = "Le mot de passe doit contenir au moins 8 caractères.";
    }
}

if (input.name === "password2") {
    const pass1 = container.querySelector('input[name="password1"]');
    if (input.value !== pass1.value) {
        isValid = false;
        errorMessage = "Les mots de passe ne correspondent pas.";
    }
}
        
        if (errorMessage) {
            isValid = false;
            input.classList.add('is-invalid');

            const errorMsg = document.createElement('div');
            errorMsg.className = 'text-danger small mt-1 dynamic-error-msg animate__animated animate__fadeInUp';
            errorMsg.style.fontSize = "0.82rem";
            errorMsg.innerText = errorMessage;

            // Placement : après le groupe (input-group ou row téléphone) ou l'input
            const placement = input.closest('.input-group') || input.closest('.row.g-0') || input;
            placement.after(errorMsg);
        }
    });
    return isValid;
}

function nextStep(step) {
    if (validateStepInputs(step - 1)) {
        showStep(step);
    }
}

function prevStep(step) {
    showStep(step);
}

// --- SYSTÈME AJAX ET VALIDATION SERVEUR ---

document.addEventListener('DOMContentLoaded', function() {
    setupLiveErrorCleanup();
    const handleFieldValidation = (form, errors) => {
        form.querySelectorAll('.is-invalid').forEach(el => el.classList.remove('is-invalid'));
        form.querySelectorAll('.dynamic-error-msg').forEach(el => el.remove());

        if (!errors) return;

        Object.keys(errors).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            if (field) {
                field.classList.add('is-invalid');
                const errorMessage = errors[fieldName][0].message || errors[fieldName][0];

                const newError = document.createElement('div');
                newError.className = 'text-danger small mt-1 dynamic-error-msg animate__animated animate__fadeIn';
                newError.innerText = errorMessage;
                
                const placement = field.closest('.input-group') || field.closest('.row.g-0') || field;
                placement.after(newError);
            }
        });

        // Téléportation vers la première erreur serveur trouvée
        if (form.querySelector('#step1 .is-invalid')) showStep(1);
        else if (form.querySelector('#step2 .is-invalid')) showStep(2);
        else if (form.querySelector('#step3 .is-invalid')) showStep(3);
        else if (form.querySelector('#step4 .is-invalid')) showStep(4);
    };
    const setupAjaxForm = (formSelector, messageSelector) => {
    // On utilise querySelector ici car ton formulaire client utilise un sélecteur CSS '#'
    const form = document.querySelector(formSelector);
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Validation locale de TOUS les steps
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

        const responseDiv = document.querySelector(messageSelector);
        const submitBtn = form.querySelector('[type="submit"]');
        const formData = new FormData(this);

        if (submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Traitement...';
        }
        
        fetch(this.action || window.location.href, {
            method: 'POST',
            body: formData,
            headers: { 
                'X-Requested-With': 'XMLHttpRequest', 
                'X-CSRFToken': formData.get('csrfmiddlewaretoken') 
            }
        })
        .then(response => response.json()) // On fait simple comme pour le Mentor
        .then(data => {
            if (data.status === 'success') {
                responseDiv.innerHTML = `<div class="alert alert-success py-2">${data.message}</div>`;
                // Utilisation de redirect_url envoyé par la vue
                setTimeout(() => window.location.href = data.redirect_url, 2000);
            } else {
                responseDiv.innerHTML = `<div class="alert alert-danger py-2 small">Veuillez corriger les erreurs.</div>`;
                if (data.errors) handleFieldValidation(form, data.errors);
            }
        })
        .catch(err => {
            console.error(err);
            responseDiv.innerHTML = '<div class="alert alert-danger py-2 small">Erreur technique de connexion.</div>';
        })
        .finally(() => { 
            // On réactive le bouton si ce n'est pas un succès (pour pouvoir corriger)
            if (submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerText = 'CRÉER MON COMPTE';
            }
        });
    });
};

// Appel pour le client
setupAjaxForm('#registration-form', '#register-message');
});
