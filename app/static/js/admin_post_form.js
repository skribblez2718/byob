document.addEventListener('DOMContentLoaded', function () {
  const container = document.getElementById('blocks-container');
  if (!container) return;

  const form = document.querySelector('.blog-form');
  const toolbar = document.querySelector('.block-toolbar');

  function prefixName(index, field) {
    const prefix = container.dataset.prefix; // e.g. content_blocks
    return `${prefix}-${index}-${field}`;
  }

  function updateIndices() {
    const items = Array.from(container.querySelectorAll('.block-item'));
    items.forEach((el, idx) => {
      el.dataset.index = String(idx);
      const orderInput = el.querySelector('.order-input');
      if (orderInput) orderInput.value = String(idx);
      // rename inputs
      el.querySelectorAll('select, input, textarea').forEach((inp) => {
        const field = inp.getAttribute('data-field');
        if (!field) return;
        inp.name = prefixName(idx, field);
        inp.id = prefixName(idx, field);
      });
    });
  }

  function setTypeVisibility(blockEl) {
    const typeSel = blockEl.querySelector('select[data-field="type"]');
    const headingRow = blockEl.querySelector('.heading-row');
    const textRow = blockEl.querySelector('.text-row');
    const imgRow = blockEl.querySelector('.image-row');
    const t = (typeSel && typeSel.value) || 'paragraph';
    if (headingRow) headingRow.style.display = (t === 'heading') ? '' : 'none';
    if (textRow) textRow.style.display = (t === 'heading' || t === 'paragraph') ? '' : 'none';
    if (imgRow) imgRow.style.display = (t === 'image') ? '' : 'none';
  }

  // Drag and drop state
  let draggedBlock = null;
  let draggedIndex = null;

  function handleDragStart(e) {
    draggedBlock = this;
    draggedIndex = Array.from(container.children).indexOf(this);
    this.classList.add('dragging');
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', this.outerHTML);
  }

  function handleDragOver(e) {
    if (e.preventDefault) {
      e.preventDefault();
    }
    e.dataTransfer.dropEffect = 'move';
    return false;
  }

  function handleDragEnter(e) {
    if (this !== draggedBlock) {
      this.classList.add('drag-over');
    }
  }

  function handleDragLeave(e) {
    this.classList.remove('drag-over');
  }

  function handleDrop(e) {
    if (e.stopPropagation) {
      e.stopPropagation();
    }

    if (draggedBlock !== this) {
      // Determine if we're inserting before or after the target
      const rect = this.getBoundingClientRect();
      const midpoint = rect.top + rect.height / 2;
      const insertAfter = e.clientY > midpoint;

      if (insertAfter) {
        this.parentNode.insertBefore(draggedBlock, this.nextSibling);
      } else {
        this.parentNode.insertBefore(draggedBlock, this);
      }

      updateIndices();
    }

    return false;
  }

  function handleDragEnd(e) {
    // Clean up
    const blocks = container.querySelectorAll('.draggable-block');
    blocks.forEach(block => {
      block.classList.remove('dragging', 'drag-over');
    });

    draggedBlock = null;
    draggedIndex = null;
  }

  function bindBlock(blockEl) {
    // Enable drag and drop
    blockEl.draggable = true;
    blockEl.classList.add('draggable-block');

    blockEl.addEventListener('dragstart', handleDragStart);
    blockEl.addEventListener('dragover', handleDragOver);
    blockEl.addEventListener('drop', handleDrop);
    blockEl.addEventListener('dragend', handleDragEnd);
    blockEl.addEventListener('dragenter', handleDragEnter);
    blockEl.addEventListener('dragleave', handleDragLeave);

    // type change
    const typeSel = blockEl.querySelector('select[data-field="type"]');
    if (typeSel) typeSel.addEventListener('change', () => setTypeVisibility(blockEl));
    setTypeVisibility(blockEl);
  }

  function createBlockEl(initial) {
    const idx = container.querySelectorAll('.block-item').length;
    const wrapper = document.createElement('div');
    wrapper.className = 'block-item draggable-block';
    wrapper.dataset.index = String(idx);
    wrapper.draggable = true;
    wrapper.innerHTML = `
      <div class="block-header">
        <div class="drag-handle" title="Drag to reorder">⋮⋮</div>
      </div>
      <div class="block-fields">
        <div class="field-row">
          <label>Type</label>
          <select class="form-select" data-field="type" name="${prefixName(idx,'type')}">
            <option value="heading">Heading</option>
            <option value="paragraph">Paragraph</option>
            <option value="image">Image</option>
          </select>
          <label>Order</label>
          <input class="form-control order-input" data-field="order" type="number" min="0" name="${prefixName(idx,'order')}" value="${idx}">
        </div>
        <div class="field-row heading-row">
          <label>Level</label>
          <select class="form-select" data-field="heading_level" name="${prefixName(idx,'heading_level')}">
            <option value="2">H2</option>
            <option value="3">H3</option>
            <option value="4">H4</option>
            <option value="5">H5</option>
          </select>
        </div>
        <div class="field-row text-row">
          <label>Text</label>
          <textarea class="form-control" rows="3" data-field="text" name="${prefixName(idx,'text')}"></textarea>
        </div>
        <div class="field-row image-row">
          <input type="hidden" data-field="existing_src" name="${prefixName(idx,'existing_src')}">
          <label>Image</label>
          <input class="form-control" type="file" accept="image/*" data-field="image" name="${prefixName(idx,'image')}">
          <label>Alt</label>
          <input class="form-control" type="text" data-field="alt" name="${prefixName(idx,'alt')}">
        </div>
      </div>
      <div class="block-controls">
        <label class="inline"><input type="checkbox" data-field="delete" name="${prefixName(idx,'delete')}"> Delete</label>
      </div>`;

    // Initialize defaults
    const typeSel = wrapper.querySelector('select[data-field="type"]');
    if (initial && initial.type) typeSel.value = initial.type;
    const lvlSel = wrapper.querySelector('select[data-field="heading_level"]');
    if (initial && initial.heading_level) lvlSel.value = initial.heading_level;
    const textAreas = wrapper.querySelectorAll('textarea[data-field="text"]');
    textAreas.forEach((ta) => { if (initial && initial.text) ta.value = initial.text; });
    const alt = wrapper.querySelector('input[data-field="alt"]');
    if (alt && initial && initial.alt) alt.value = initial.alt;
    const existing = wrapper.querySelector('input[data-field="existing_src"]');
    if (existing && initial && initial.existing_src) existing.value = initial.existing_src;

    container.appendChild(wrapper);
    bindBlock(wrapper);
    setTypeVisibility(wrapper);
    updateIndices();
  }

  if (toolbar) {
    toolbar.addEventListener('click', function (e) {
      const btn = e.target.closest('button[data-action]');
      if (!btn) return;
      const action = btn.dataset.action;
      if (action === 'add-heading') createBlockEl({ type: 'heading', heading_level: '2' });
      if (action === 'add-paragraph') createBlockEl({ type: 'paragraph' });
      if (action === 'add-image') createBlockEl({ type: 'image' });
    });
  }

  // Bind existing blocks rendered by server
  Array.from(container.querySelectorAll('.block-item')).forEach(bindBlock);
  updateIndices();
});
