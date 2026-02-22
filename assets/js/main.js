// Mobile menu toggle
$(document).ready(function() {
  $('[data-nav-menu]').on('click', function() {
    var target = $(this).attr('data-nav-menu');
    $(target).slideToggle();
  });

  // Magnific popup for gallery images
  if ($.fn.magnificPopup) {
    $('.img-pop-up').magnificPopup({
      type: 'image',
      gallery: {
        enabled: true
      }
    });

    $('.popup-video').magnificPopup({
      type: 'iframe'
    });
  }
});
