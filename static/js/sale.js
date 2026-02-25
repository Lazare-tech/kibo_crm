    function switchPosTab(tab, element) {
        // Gestion des sections
        document.querySelectorAll('.pos-section').forEach(s => s.classList.remove('active'));
        document.getElementById('section-' + tab).classList.add('active');
        
        // Gestion du menu mobile
        if(element) {
            document.querySelectorAll('.pos-nav-item').forEach(i => i.classList.remove('active'));
            element.classList.add('active');
        }
    }
    //
    function markAsSelected(element) {
        element.classList.add('product-selected-flash');
        setTimeout(() => {
            element.classList.remove('product-selected-flash');
        }, 300); // L'effet dure 300ms
    }

    // 2. Mise à jour du badge du panier
    function updateCartBadge() {
        // On compte le nombre d'articles dans le panier (lignes du tableau)
        const cartItems = document.querySelectorAll('#cart-items tr').length;
        const badge = document.getElementById('cart-count');
        
        if (badge) {
            badge.innerText = cartItems;
            
            // Animation du badge
            badge.classList.remove('badge-pop');
            void badge.offsetWidth; // Trigger reflow pour relancer l'animation
            badge.classList.add('badge-pop');
            
            // Cache le badge si panier vide
            badge.style.display = cartItems > 0 ? 'inline-block' : 'none';
        }
    }

    // Initialisation au chargement de la page
    document.addEventListener('DOMContentLoaded', updateCartBadge);
    
    // Si tu supprimes un produit du panier, il faut aussi mettre à jour le badge
    document.body.addEventListener('htmx:afterOnLoad', function(evt) {
        if (evt.detail.target.id === 'cart-items') {
            updateCartBadge();
        }
    });

    // Ta fonction existante
    function switchPosTab(tab, element) {
        document.querySelectorAll('.pos-section').forEach(s => s.classList.remove('active'));
        document.getElementById('section-' + tab).classList.add('active');
        if(element) {
            document.querySelectorAll('.pos-nav-item').forEach(i => i.classList.remove('active'));
            element.classList.add('active');
        }
    }
